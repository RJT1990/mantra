import numpy as np

from mantraml.data.Dataset import Dataset


class ExampleDataset(Dataset):
    """
    This class implements dataset processing methods for the Example dataset
    """

    # These class variables contain metadata on the Dataset
    name = 'testdata'
    tar_name = 'example_images' # e.g 'example_images' for 'example_images.tar.gz'
    data_type = 'png-images' # optional labelling of the datatype for free methods - see Mantra docs
    has_labels = True

    def __init__(self, name, **kwargs):       
        """
        This initialises an instance of the Dataset

        Parameters
        -----------
        name - str
            The folder name for the dataset
        """

        # this __init__method performs extraction on the dataset and some basic processing using
        # the mantra Dataset class

        super().__init__(name=name, **kwargs)

    def extract_inputs(self, training=True):
        """
        This method extracts inputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Parameters
        --------
        training - bool
            If True, returns training data, else test data

        Returns
        --------
        np.ndarray - of data inputs (X vector)
        """

        # put your logic here for extracting features from the data in self.data_path
        # you should return a np.ndarray of features (X)

        return np.array([1,2,3,4,5])

    def extract_outputs(self, training=True):
        """
        This method extracts outputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Parameters
        --------
        training - bool
            If True, returns training data, else test data

        Returns
        --------
        np.ndarray - of data inputs (y vector)
        """

        # put your logic here for extracting labels (the target) from the data in self.data_path
        # you should return a np.ndarray of labels (y)

        return np.array([2,4,6,8,10])
