import inspect
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os
import tarfile
import shutil

from collections import Counter

from mantraml.core.hashing.MantraHashed import MantraHashed

from .consts import DATA_TEST_MSGS

TAR_FILES_TO_CHECK = 100


def cachedata(function):
    """
    This decorator saves the output of a @property decorated function "my_data" to a private location "_my_data".
    When we call the function again, we simply retrieve the output from RAM instead of doing the calculation again. 
    """

    @property
    def wrapper(*args, **kwargs):
        try:
            stored_data = getattr(args[0], '_%s' % function.__name__)
        except AttributeError:
            setattr(args[0], '_%s' % function.__name__, None)
            stored_data = getattr(args[0], '_%s' % function.__name__)

        if stored_data is not None:
            return stored_data
        else:
            stored_data = function(*args, **kwargs)
            setattr(args[0], '_%s' % function.__name__, stored_data)
            return stored_data

    return wrapper


class Dataset:
    """
    This class contains methods for processing, retrieving and storing datasets using Mantra.

    The key class variable we process is Dataset.files. If we have content in this folder then we loop over these files
    and perform the following operations:

    - Is the folder outside the directory, or in it? 
            - We can refer to files outside of the directory, e.g. when using Datasets in Jupyter Notebooks. If so, we set up a
              temporary .tempmantra folder to extract the data to when we initialise a Dataset.

            - If the files paths have no directories, we assume they are located in the raw/ subdirectory within a data project.

    - Is the file a tar.gz file? If the user specifies tarred files in their files list, then we make a note that this is a file
    that should be extracted into its own folder. This is so we can access the contents during traiing.
    """

    data_type = None

    def __init__(self, **kwargs):

        self.folder_name = inspect.getfile(self.__class__).split('/')[-2]
        self.configure_files_attribute()

        self.data_from_files = False
        self.data_outside_project = False

        if self.files:
            self.data_from_files = True

            self.outside_project = False
            self.extract_file_dict = {}

            for file in self.files:
                self.configure_data_directory(file)

        if self.data_from_files:
            self.configure_files_data(**kwargs)
            self.extract_file_data()

        # Training and test data
        self._X = None
        self._y = None

    def __getitem__(self, idx):
        """
        Returs a tuple of data based on the index

        Parameters
        --------
        idx - int
            Index of the dataset

        Returns
        --------
        tuple - the indexed features matrix X, and the indexed features matrix y
        """

        return (self.X[idx], self.y[idx])

    def __len__(self):
        """
        This method returns the number of examples in the data

        Returns
        --------
        int - the number of examples in the dataset
        """

        return self.X.shape[0]

    @cachedata
    def X(self):
        """
        This method extracts inputs X from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs
        """

        return None

    @cachedata
    def y(self):
        """
        This method extracts outputs y from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs
        """

        return None

    @classmethod
    def denormalize_image(cls, image, normalized=True):
        """
        Denormalizes an image

        Parameters
        -----------
        image - np.ndarray representing the image

        normalized - bool
            True if the image was originally normalized, False otherwise

        Returns
        -----------
        np.ndarray - applying the denormalization
        """

        if normalized:
            return (image+1)*127.5
        else:
            return image

    def configure_core_arguments(self, args):
        """
        This method adds core training attributes from an argument parser namespace (args) such as feature information
        for Tabular Datasets

        Parameters
        -----------
        args - Argument parser namespace
            Containing training arguments such as feature column names, the target column names

        Returns
        -----------
        void - update self with new attributes
        """

        if args.features is not None:
            self.features = args.features

        if args.target is not None:
            self.target = args.target

        if args.feature_indices is not None:
            self.feature_indices = args.feature_indices

        if args.target_index is not None:
            self.target_index = args.target_index

        if args.image_dim is not None:
            self.image_dim = tuple([int(el) for el in tuple(args.image_dim)])
            self.image_shape = (self.image_dim[0], self.image_dim[1], self.n_color_channels)

    def configure_data_directory(self, file):
        """
        Configures the data directory to use for the Dataset
        
        Parameters
        --------
        training - bool
            If True, returns training data, else test data
        """

        if '/' in file:
            self.data_outside_project = True
            self.data_dir = '%s/.tempmantra/' % os.getcwd()
        else:
            self.data_outside_project = False
            self.data_dir = '%s/data/%s/' % (os.getcwd(), self.folder_name)

        if '.tar.gz' in file:
            self.extract_file_dict[file] = True
        else:
            self.extract_file_dict[file] = False

    def configure_files_attribute(self):
        """
        Configures the files attribute depending on the dataset type
        """

        if not hasattr(self, 'files'):

            if hasattr(self, 'image_dataset'):
                self.files = [self.image_dataset]
            else:
                self.files = None

        else:
            if not self.files and hasattr(self, 'image_dataset'):
                self.files = [self.image_dataset]

    def configure_files_data(self, execute=True, **kwargs):
        """
        This method configures the data based on dataset details from a file

        Parameters
        --------
        execute - bool
            Performs file level operations to find the file format

        Returns
        --------
        void - updates the class with attributes
        """

        if 'images' == self.data_type:

            if execute:
                if not hasattr(self, 'image_dataset'):
                    self.image_dataset = self.files[0]

                self.find_image_file_format()
            else:
                self.n_color_channels = 3

            # Set default image attributes

            if not hasattr(self, 'image_dim'): # no default image_dimension
                self.image_dim = (32, 32)

            if not hasattr(self, 'normalize'):
                self.normalize = True # we normalize the image for use in training

            # Retrieve custom user arguments

            self.image_dim = kwargs.get('image_dim', self.image_dim)
            self.image_shape = kwargs.get('image_shape', (self.image_dim[0], self.image_dim[1], self.n_color_channels))
            self.normalize = kwargs.get('normalize', self.normalize)

    def extract_file_data(self):
        """
        This method extracts data from the files list, and checks hashes based on old extractions

        Returns
        --------
        void - extracts files and stores extract location
        """

        self.hash_location = '%s%s' % (self.data_dir, 'raw/hash')
        self.raw_data_path = '%s%s' % (self.data_dir, 'raw')
        self.extracted_data_path = '%s%s' % (self.raw_data_path, '/.extract')

        is_hash = os.path.isfile(self.hash_location)
        is_extract_folder = os.path.exists(self.extracted_data_path)
        is_data_folder = os.path.exists(self.data_dir)

        if not is_extract_folder:
            os.mkdir(self.extracted_data_path)

        file_hashes = self.get_data_dependency_hashes(is_extract_folder=is_extract_folder, is_hash=is_hash)
        final_hash = MantraHashed.get_256_hash_from_string(''.join(file_hashes))

        # If there is no hash then we store the hash

        if not is_hash:
            hash_file = open(self.hash_location, 'w')
            hash_file.write(final_hash)
            hash_file.close()

        # If there is no extract folder then we create one and copy the files over

        if not is_extract_folder:
            for file in self.files:
                file_path = '%s/%s' % (self.raw_data_path, file)
                shutil.copy(file_path, self.extracted_data_path)
            return

        hash_file = open(self.hash_location, 'r')
        old_hash = hash_file.read()
        hash_file.close()

        # If the hash of dependency files hasn't changed, we are good to go; else we copy the new files over

        if old_hash == final_hash:
            return

        else:

            for file in self.files:
                file_path = '%s/%s' % (self.raw_data_path, file)
                shutil.copy(file_path, self.extracted_data_path)

    def extract_tar_file(self, file):
        """
        This method extracts a tar file to a location in a raw folder
        
        Parameters
        --------
        file - str
            Path to the tar file to open and extract to the raw/ folder within the dataset project
        """

        tar = tarfile.open(file, mode='r')

        # check tar contains files at the top directory
        files_at_top = False

        for member in tar.getmembers():
            if '/' not in member.name and member.isfile():
                files_at_top = True
                break

        if os.path.isdir(self.extracted_data_path):
            shutil.rmtree(self.extracted_data_path)

        if files_at_top:
            tar.extractall(path=self.extracted_data_path)
        else:
            top_level_dir = os.path.commonprefix(tar.getnames())
            tar.extractall(path=self.raw_data_path)
            os.rename('%sraw/%s' % (self.data_dir, top_level_dir), '%sraw/%s' % (self.data_dir, '.extract'))

    def find_image_file_format(self):
        """
        This method finds the image file format from the data referenced in Dataset class. We take a sample
        of files in a tar.gz directory and record the most popular file type. The resulting file format is 
        stored in self.file_format - .jpg - and the number of color channels - to self.n_color_channels.
        """

        tar = tarfile.open('%s%s/%s' % (self.data_dir, 'raw', self.image_dataset), mode='r')
        sample_files = [mem for mem in tar.getmembers() if mem.isfile()]
        sample_file_extensions = [mem.path.split('.')[-1] for mem in sample_files[:TAR_FILES_TO_CHECK] if '.' in mem.path]
        extension_count = Counter(sample_file_extensions)
        self.file_format = '.%s' % extension_count.most_common(1)[0][0]

        if self.file_format in ['.jpg', '.jpeg']:
            self.n_color_channels = 3
        elif self.file_format == '.png':
            self.n_color_channels = 4

    def get_data_dependency_hashes(self, is_extract_folder, is_hash):
        """
        This method obtains a list of hashes of the file dependencies (Dataset.files) specified in the dataset.

        Parameters
        --------

        is_extract_folder - bool
            Whether an .extract folder currently exists within the data project folder

        is_hash - bool
            Whether a concatenated hash file exists for the raw data dependencies

        Returns
        --------
        list of strs - containing the hashes of the files in Dataset.files, hash of tar if exists
        """

        file_hashes = []

        for file in sorted(self.files):

            file_path = '%s/%s' % (self.raw_data_path, file)

            if not os.path.isfile(file_path):
                raise IOError('The following file does no exist:  %s' % file)

            tar_hash = MantraHashed.get_256_hash_from_file(file_path)
            file_hashes.append(tar_hash)

            if not is_extract_folder or not is_hash:
                if self.extract_file_dict[file]:
                    self.extract_tar_file(file_path)
                else:
                    shutil.copy(file_path, self.extracted_data_path)

        return file_hashes

    def plot_image_sample(sample):
        """
        Plots an image sample

        Parameters
        -----------
        sample : np.ndarray
            The image in numpy format
        """

        grid_dim = np.ceil(np.sqrt(n)).astype('int')

        fig = plt.figure(figsize=(8, 8))
        plt.axis('off')

        for i in range(grid_dim*grid_dim):

            if (i+1) > n:
                continue

            fig.add_subplot(grid_dim, grid_dim, i+1)

            if len(sample[i].shape) == 2:
                plt.imshow(self.denormalize_image(sample[i], normalized=self.normalize).astype(np.uint8), cmap='gray')
                plt.show()
            else:
                plt.imshow(self.denormalize_image(sample[i], normalized=self.normalize).astype(np.uint8))
            
        plt.show()

    def sample(self, n=5):
        """
        This method draws a sample from the data

        Parameters
        -----------
        n : int
            Number of datapoints to sample

        Returns
        -----------
        either a matplotlib plot if it is an image data type, else a dataframe or np.ndarray object
        """

        if self.X is None:
            raise ValueError('The data attribute .X is None!')

        x_sample = self.X[np.random.randint(self.X.shape[0], size=n)]

        if self.data_type == 'images':
            self.plot_image_sample(sample=x_sample)
        
        elif self.data_type == 'tabular':
            df = pd.DataFrame(x_sample)

            if self.features:
                df.columns = self.features
            if self.features_index:
                df.columns = self.df.columns[self.features_index]

            return df

        else:
            return x_sample