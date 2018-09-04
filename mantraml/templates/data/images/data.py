import numpy as np

from mantraml.data import Dataset, cachedata
from mantraml.data import ImageDataset


class MyImageDataset(ImageDataset):
    # core metadata
    data_name = 'My Image Dataset'
    data_tags = ['example', 'new', 'images']
    files = ['example_dataset.tar.gz']
    image_dataset = 'example_dataset.tar.gz' # referring to the file that contains the images

    # additional default data
    has_labels = False
    image_dim = (128, 128)
    normalized = True

    @cachedata
    def y(self):
        # return your labels here as an np.ndarray
        # if no labels, e.g. generative models, then you can remove this method
        return