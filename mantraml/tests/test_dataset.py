import os
import numpy as np
import pandas as pd

from mantraml.data import Dataset, cachedata

import pytest


class MyDataset(Dataset):

    files = []

class MySecondDataset(Dataset):

    files = []
    data_type = 'images'

    @cachedata
    def X(self):
        return np.array([1,2,3,4,5])


def test_configure_core_arguments():

    class MockArgParser:

        def __init__(self):
            self.features = ['column_a', 'column_b']
            self.target = 'column_z'
            self.feature_indices = [1, 2, 3]
            self.target_index = 0
            self.image_dim = [128, 128]

    my_data = MyDataset()
    my_data.configure_core_arguments(MockArgParser())

    assert(my_data.features == ['column_a', 'column_b'])
    assert(my_data.feature_indices == [1, 2, 3])
    assert(my_data.target_index == 0)
    assert(my_data.target == 'column_z')

def test_dataset_init():

    dataset_name = 'testdata'

    my_data = MyDataset()

    # Folder name and files
    assert(my_data.files == [])
    assert(my_data.folder_name == 'tests')

    # Set an image dataset attribute, and test the configure_file_attributes
    # this should automatically fill files with the new dataset

    my_data.image_dataset = 'images.tar.gz'
    my_data.configure_files_attribute()
    assert(my_data.files[0] == 'images.tar.gz')

def test_configure_data_directory():

    dataset_name = 'testdata'

    my_data = MyDataset()
    my_data.extract_file_dict = {}

    my_data.configure_data_directory('/home/ubuntu/my_table.csv')
    assert(my_data.data_outside_project)
    assert(my_data.data_dir == '%s/.tempmantra/' % os.getcwd())
    assert(my_data.extract_file_dict['/home/ubuntu/my_table.csv'] is False)

    my_data.configure_data_directory('/home/ubuntu/my_files.tar.gz')
    assert(my_data.data_outside_project)
    assert(my_data.data_dir == '%s/.tempmantra/' % os.getcwd())
    assert(my_data.extract_file_dict['/home/ubuntu/my_files.tar.gz'] is True)

    my_data.configure_data_directory('my_table.csv')
    assert(my_data.data_outside_project is False)
    assert(my_data.data_dir == '%s/data/%s/' % (os.getcwd(), my_data.folder_name))
    assert(my_data.extract_file_dict['my_table.csv'] is False)

    my_data.configure_data_directory('my_files.tar.gz')
    assert(my_data.data_outside_project is False)
    assert(my_data.data_dir == '%s/data/%s/' % (os.getcwd(), my_data.folder_name))
    assert(my_data.extract_file_dict['my_files.tar.gz'] is True)

def test_normalize_images():

    dataset_name = 'testdata'
    my_data = MyDataset()

    image = np.array([[0.432, 0.543, 0.234], [0.32432, 0.76765, 0.45435], [0.43243, 0.43432, 0.132131]])

    de_normalized_image = my_data.denormalize_image(image=image, normalized=True)

    assert(de_normalized_image.shape == image.shape)
    assert(np.isclose(de_normalized_image[0][0], 182.58))
    assert(np.isclose(de_normalized_image[0][1], 196.7325))

    de_normalized_image = my_data.denormalize_image(image=image, normalized=False)

    assert(de_normalized_image.shape == image.shape)
    assert(de_normalized_image[0][0] == 0.432)
    assert(de_normalized_image[0][1] == 0.543)

def test_dataset_image_attributes():

    dataset_name = 'testdata'

    my_data = MySecondDataset()
    my_data.configure_files_data(execute=False, **{'image_dim': (256, 100), 'normalize': True})
    assert(my_data.image_shape == (256, 100, 3))
    assert(my_data.normalize)

def test_dataset_len():

    dataset_name = 'testdata'

    my_data = MySecondDataset()

    assert(len(my_data) == 5) # the array size of the example dataset