import numpy as np

from mantraml.data.Dataset import Dataset, datamethod
from mantraml.data.ImageDataset import ImageDataset


class MyImageDataset(ImageDataset):
    # core metadata
    dataset_name = 'My Image Dataset'
    dataset_tags = ['example', 'new', 'images']
    files = ['example_dataset.tar.gz']
    image_dataset = 'example_dataset.tar.gz' # referring to the file that contains the images

    # additional default data
    has_labels = False
    image_dim = (128, 128)
    normalized = True

    @datamethod
    def y(self):
        # return your labels here as an np.ndarray
        # if no labels, e.g. generative models, then you can remove this method