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


def datamethod(function):
    """
    Decorator for data loading - currently saves to RAM on the first call, and if called again, loads the saved object
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
    This class contains methods for processing, retrieving and storing datasets 
    """

    def __init__(self, **kwargs):

        self.folder_name = inspect.getfile(self.__class__).split('/')[-2]

        if not hasattr(self, 'files'):

            if hasattr(self, 'image_dataset'):
                self.files = [self.image_dataset]
            else:
                self.files = None

        self.data_from_files = False
        self.data_outside_project = False

        if self.files is not None:
            self.data_from_files = True

            self.outside_project = False
            self.extract_file_dict = {}

            for file in self.files:
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

        if self.data_from_files:
            self.configure_file_data(**kwargs)
            self.extract_file_data()

        # Training and test data
        self._X = None
        self._y = None

    def __getitem__(self, idx):
        """
        Returs a tuple of data based on the index
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

    @datamethod
    def X(self):
        """
        This method extracts inputs X from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs
        """

        return None

    @datamethod
    def y(self):
        """
        This method extracts outputs y from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs
        """

        return None

    def configure_file_data(self, **kwargs):
        """
        This method configures the data based on dataset details from a file

        Returns
        --------
        void - updates the class with attributes
        """

        if 'images' == self.dataset_type:

            # Find Iamage File Format

            # if no image dataset file, assume user has one file in files field
            if not hasattr(self, 'image_dataset'):
                self.image_dataset = self.files[0]

            tar = tarfile.open('%s%s/%s' % (self.data_dir, 'raw', self.image_dataset), mode='r')
            sample_files = [mem for mem in tar.getmembers() if mem.isfile()]
            sample_file_extensions = [mem.path.split('.')[-1] for mem in sample_files[:TAR_FILES_TO_CHECK] if '.' in mem.path]
            extension_count = Counter(sample_file_extensions)
            self.file_format = '.%s' % extension_count.most_common(1)[0][0]

            if self.file_format in ['.jpg', '.jpeg']:
                self.n_color_channels = 3
            elif self.file_format == '.png':
                self.n_color_channels = 4

            # Set default image attributes

            if not hasattr(self, 'image_dim'): # no default image_dimension
                self.image_dim = (32, 32)

            if not hasattr(self, 'normalize'):
                self.normalize = False

            # Retrieve custom user arguments

            self.image_dim = kwargs.get('image_dim', self.image_dim)
            self.image_shape = kwargs.get('image_shape', (self.image_dim[0], self.image_dim[1], self.n_color_channels))
            self.normalize = kwargs.get('normalize', self.normalize)

    def extract_tar_file(self, file):
        """
        This method extracts a tar file to a location in a raw folder
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

    @classmethod
    def get_data_folder_hash(cls, data_dir, files):
        """
        This method takes files, and works out the hash of the files collectively 

        We use this for the cloud data upload to check if the dataset is synced between both locations
        """

        file_hashes = []

        for file in sorted(files):

            if not os.path.isfile('%sraw/%s' % (data_dir, file)):
                raise IOError('The following file that was referenced in your Dataset class does not exist: %s' % file)

            tar_hash = MantraHashed.get_256_hash_from_file('%sraw/%s' % (data_dir, file))
            file_hashes.append(tar_hash)

        return MantraHashed.get_256_hash_from_string(''.join(file_hashes))

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

        if not is_data_folder:
            os.mkdir(self.data_dir)
            os.mkdir(self.raw_data_path)
            os.mkdir(self.extracted_data_path)

        file_hashes = []

        # GET THE HASH OF THE FOLDER
        # TODO : ignore .extract folder and inner-hash file for the tar.gz

        for file in sorted(self.files):

            file_path = '%s/%s' % (self.raw_data_path, file)

            if not os.path.isfile(file_path):
                raise IOError('The following file does no exist:  %s' % file)

            if not is_extract_folder or not is_hash:
                tar_hash = MantraHashed.get_256_hash_from_file(file_path)
                file_hashes.append(tar_hash)

                if self.extract_file_dict[file]:
                    self.extract_tar_file(file_path)
                else:
                    shutil.copy(file_path, self.extracted_data_path)

        final_hash = MantraHashed.get_256_hash_from_string(''.join(file_hashes))

        # IF THERE IS NO HASH THEN WE STORE THE HASH

        if not is_hash:
            hash_file = open(self.hash_location, 'w')
            hash_file.write(tar_hash)
            hash_file.close()

        if not is_extract_folder:
            for file in self.files:
                file_path = '%s/%s' % (self.raw_data_path, file)
                shutil.copy(file_path, self.extracted_data_path)
            return

        hash_file = open(self.hash_location, 'r')
        old_hash = hash_file.read()
        hash_file.close()

        if old_hash == final_hash:
            return

        else:

            for file in self.files:
                file_path = '%s/%s' % (self.raw_data_path, file)
                shutil.copy(file_path, self.extracted_data_path)

    def extract_outputs(self, training=True):
        """
        This method extracts outputs (or 'labels') from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Parameters
        --------
        training - bool
            If True, returns training data, else test data

        Returns
        --------
        np.ndarray - of data outputs/labels
        """

        return None

    def input_tests(self):
        """
        Test the data output of the class
        """

        try:
            assert(self.X is not None)
        except AssertionError:
            raise AssertionError(DATA_TEST_MSGS['empty_inputs'])

        try:
            assert(isinstance(self.X, np.ndarray))
        except AssertionError:
            raise AssertionError(DATA_TEST_MSGS['non_numpy_input'])

        try:
            assert(self.X.shape[0] > 0)
        except AssertionError:
            raise AssertionError(DATA_TEST_MSGS['zero_len_input'])

        try:
            assert(np.nanstd(self.X) > 0)
        except AssertionError:
            raise AssertionError(DATA_TEST_MSGS['zero_std_input'])

        if np.isnan(self.X).sum() > 0:
            print(DATA_TEST_MSGS['input_contains_nans'])

    def output_tests(self):
        """
        Test the data output of the class
        """

        if self.y is None:
            if hasattr(self, 'has_labels'):
                if self.has_labels is True:
                    raise AssertionError(DATA_TEST_MSGS['empty_outputs'])
                else:
                    pass
            else:
                raise AssertionError(DATA_TEST_MSGS['empty_outputs_and_no_flag'])

        if hasattr(self, 'has_labels'):
            if self.has_labels is True:
                
                try:
                    assert(isinstance(self.y, np.ndarray))
                except AssertionError:
                    raise AssertionError(DATA_TEST_MSGS['non_numpy_output'])

                try:
                    assert(self.y.shape[0] > 0)
                except AssertionError:
                    raise AssertionError(DATA_TEST_MSGS['zero_len_output'])

                try:
                    assert(np.nanstd(self.y) > 0)
                except AssertionError:
                    raise AssertionError(DATA_TEST_MSGS['zero_std_output'])

                if np.isnan(self.y).sum() > 0:
                    print(DATA_TEST_MSGS['output_contains_nans'])

                try:
                    assert(self.y.shape[0] == self.X.shape[0])
                except AssertionError:
                    raise AssertionError(DATA_TEST_MSGS['input_output_lens'] % (self.y.shape[0], self.X.shape[0]))

    def test(self):
        """
        This method performs a number of tests on the user's Dataset to ensure it is in the right format to be used
        for Mantra models
        """

        self.input_tests()
        self.output_tests()

        print('[+] All tests passed')

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

        if self.dataset_type == 'images':

            grid_dim = np.ceil(np.sqrt(n)).astype('int')

            fig = plt.figure(figsize=(8, 8))
            plt.axis('off')

            for i in range(grid_dim*grid_dim):

                if (i+1) > n:
                    continue

                fig.add_subplot(grid_dim, grid_dim, i+1)

                if len(x_sample[i].shape) == 2:
                    plt.imshow(self.denormalize_image(x_sample[i], normalized=self.normalize).astype(np.uint8), cmap='gray')
                    plt.show()
                else:
                    plt.imshow(self.denormalize_image(x_sample[i], normalized=self.normalize).astype(np.uint8))
                
            plt.show()
        
        elif self.dataset_type == 'tabular':

                df = pd.DataFrame(x_sample)

                if self.features:
                    df.columns = self.features
                if self.features_index:
                    df.columns = self.df_train.columns[self.features_index]

                return df

        else:
            return x_sample