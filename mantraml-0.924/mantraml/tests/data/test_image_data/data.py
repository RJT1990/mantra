import numpy as np

from mantraml.data.ImageDataset import ImageDataset


class MyImageDataset(ImageDataset):

    # These class variables contain metadata on the Dataset
    name = 'test_image_data'
    tar_name = 'example_images' # e.g 'example_images' for 'example_images.tar.gz'
    data_type = 'images' # optional labelling of the datatype for free methods - see Mantra docs
    has_labels = False


    def __init__(self, name, image_dim=(128, 128), **kwargs):       
        """
        This initialises an instance of a TabularDataset

        Parameters
        -----------
        
        name - str
            The folder name for the dataset

        image_dim - tuple
            The desired image dimension (height, width) e.g. (64, 64) for 64 x 64 resolution
        """

        super().__init__(name=name, image_dim=image_dim, **kwargs)