import os
import numpy as np
import pandas as pd

from mantraml.data.Dataset import Dataset
from mantraml.tests.data.testdata.data import ExampleDataset
from mantraml.tests.data.test_tabular_data.data import MyDataset
from mantraml.tests.data.test_image_data.data import MyImageDataset

import pytest

@pytest.mark.skip(reason="Fix this after the simplifcation refactor")
def test_dataset_init():

    dataset_name = 'testdata'

    my_data = ExampleDataset(dataset_name)
    assert(my_data.name == dataset_name)
    assert(my_data.data_dir == os.getcwd() + '/data/%s/' % dataset_name)
    assert(my_data.tar_dir == os.getcwd() + '/data/%s/raw/example_images.tar.gz' % dataset_name)

    # because the example dataset is png images
    assert(my_data.n_color_channels == 4)
    assert(my_data.file_format == '.png')

@pytest.mark.skip(reason="Fix this after the simplifcation refactor")
def test_dataset_image_attributes():

    dataset_name = 'testdata'

    my_data = ExampleDataset(dataset_name, image_size=256)
    assert(my_data.image_size == 256)
    assert(my_data.image_shape == (256, 256, 4))

def test_n_examples():

    dataset_name = 'testdata'

    my_data = ExampleDataset(dataset_name, image_size=256)

    assert(my_data.n_examples == 5) # the array size of the example dataset

def test_path_locations():

    dataset_name = 'testdata'

    my_data = ExampleDataset(dataset_name, image_size=256)
    data_dir =  os.getcwd() + '/data/%s/' % dataset_name

    assert(my_data.hash_location == '%s%s' % (data_dir, 'raw/hash'))
    assert(my_data.data_path == '%s%s' % (data_dir, 'raw/.extract'))

def test_tabular_dataset():

    dataset_name = 'test_tabular_data'

    my_data = MyDataset(dataset_name)

    # the metadata settings in MyDataset class
    assert(my_data.name == dataset_name)
    assert(my_data.tar_name == 'dataset')
    assert(my_data.data_type == 'tabular')
    assert(my_data.has_labels == True)

    # tabular data fields
    assert(my_data.file_name == 'dataset.csv')
    assert(my_data.target == 'team_1_score')
    assert(my_data.features == ['d_ability_1', 'd_ability_3', 'is_february'])
    assert(my_data.target_index == None)
    assert(my_data.features_index == None)
    assert(my_data.training_test_split == 0.75)

    # tabular data...data
    assert(isinstance(my_data.df_train, pd.DataFrame))
    assert(isinstance(my_data.df_test, pd.DataFrame))
    assert(my_data.df_train.shape[0] > my_data.df_test.shape[0])
    assert(isinstance(my_data.X, np.ndarray))
    assert(isinstance(my_data.y, np.ndarray))
    assert(isinstance(my_data.X_test, np.ndarray))
    assert(isinstance(my_data.y_test, np.ndarray))
    assert(my_data.X.shape[0] == my_data.df_train.shape[0])
    assert(my_data.X_test.shape[0] == my_data.df_test.shape[0])
    assert(my_data.y.shape[0] == my_data.df_train.shape[0])
    assert(my_data.y_test.shape[0] == my_data.df_test.shape[0])

    assert(my_data.df_train.shape[0] > my_data.df_test.shape[0])

@pytest.mark.skip(reason="Fix this after the simplifcation refactor")
def test_image_dataset():

    dataset_name = 'test_image_data'

    my_data = MyImageDataset(dataset_name)
    # the metadata settings in MyDataset class

    assert(my_data.name == dataset_name)
    assert(my_data.training_test_split == 0.75)

    # tabular data...data
    assert(isinstance(my_data.X, np.ndarray))
    assert(isinstance(my_data.X_test, np.ndarray))

    # dataset size (total number of images in the dataset here is 4) 
    assert(my_data.X.shape[0] == 3)
    assert(my_data.X_test.shape[0] == 1)

    # image dimension and formatting
    assert(my_data.X[0].shape == (128, 128, 4))
    assert(my_data.X_test[0].shape == (128, 128, 4))

    assert(my_data.X[0].shape == (128, 128, 4))
    assert(my_data.X_test[0].shape == (128, 128, 4))

    assert(my_data.image_dim == (128, 128))
    assert(my_data.image_shape == (128, 128, 4))
    assert(my_data.file_format == '.png')
    assert(my_data.n_color_channels == 4)

    # Let's test now if we put in a custom input dimension, and whether it resizes the image correctly
    # We'll try a lower dimension; a higher dimension, and an uneven dimension

    for image_dim in [(64, 64), (256, 256), (64, 89)]:

        my_data = MyImageDataset(dataset_name, image_dim=image_dim)

        assert(my_data.X[0].shape == (image_dim[0], image_dim[1], 4))
        assert(my_data.X_test[0].shape == (image_dim[0], image_dim[1], 4))

        assert(my_data.X[0].shape == (image_dim[0], image_dim[1], 4))
        assert(my_data.X_test[0].shape == (image_dim[0], image_dim[1], 4))

        assert(my_data.image_dim == image_dim)
        assert(my_data.image_shape == (image_dim[0], image_dim[1], 4))