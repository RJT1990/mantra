import os
import numpy as np
import pandas as pd
import yaml

from mantraml.tasks import Task

import pytest


class MockData:

    X = np.array([[1,2,3,4,5,6,7,8,9], [2,3,4,5,6,7,8,9,10]]).T
    y = np.array([10, 11, 12, 13, 14, 15, 16, 17, 18])

    def __len__(self):
        return len(self.y)

def test_training_split_regular():

    my_task = Task(data=MockData())
    my_task.training_split = (0.33, 0.33, 0.34)

    X_train = my_task.X_train
    X_val = my_task.X_val
    X_test = my_task.X_test

    y_train = my_task.y_train
    y_val = my_task.y_val
    y_test = my_task.y_test

    assert(X_train.shape == (2, 2))
    assert(np.all(X_train == np.array([[1, 2], [2, 3]])))

    assert(X_val.shape == (3, 2))
    assert(np.all(X_val == np.array([[3, 4], [4, 5], [5, 6]])))

    assert(X_test.shape == (4, 2))
    assert(np.all(X_test == np.array([[6, 7], [7, 8], [8, 9], [9, 10]])))

    assert(y_train.shape == (2, ))
    assert(np.all(y_train == np.array([10, 11])))

    assert(y_val.shape == (3, ))
    assert(np.all(y_val == np.array([12, 13, 14])))

    assert(y_test.shape == (4, ))
    assert(np.all(y_test == np.array([15, 16, 17, 18])))

def test_training_split_no_val():

    my_task = Task(data=MockData())
    my_task.training_split = (0.7, 0, 0.3)

    X_train = my_task.X_train
    X_val = my_task.X_val
    X_test = my_task.X_test

    y_train = my_task.y_train
    y_val = my_task.y_val
    y_test = my_task.y_test

    assert(X_train.shape == (6, 2))
    assert(np.all(X_train == np.array([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7]])))

    assert(X_val.shape == (0, 2))

    assert(X_test.shape == (3, 2))
    assert(np.all(X_test == np.array([[7, 8], [8, 9], [9, 10]])))

    assert(y_train.shape == (6, ))
    assert(np.all(y_train == np.array([10, 11, 12, 13, 14, 15])))

    assert(y_val.shape == (0, ))

    assert(y_test.shape == (3, ))
    assert(np.all(y_test == np.array([16, 17, 18])))

def test_training_split_no_val_or_test():

    my_task = Task(data=MockData())
    my_task.training_split = (1.0, 0, 0.0)

    X_train = my_task.X_train
    X_val = my_task.X_val
    X_test = my_task.X_test

    y_train = my_task.y_train
    y_val = my_task.y_val
    y_test = my_task.y_test

    assert(X_train.shape == (9, 2))
    assert(np.all(X_train == np.array([[1, 2], [2, 3], [3, 4], [4, 5], [5, 6], [6, 7], [7, 8], [8, 9], [9, 10]])))

    assert(X_val.shape == (0, 2))

    assert(X_test.shape == (0, 2))

    assert(y_train.shape == (9, ))
    assert(np.all(y_train == np.array([10, 11, 12, 13, 14, 15, 16, 17, 18])))

    assert(y_val.shape == (0, ))

    assert(y_test.shape == (0, ))

def test_indices_attribute():

    my_task = Task(data=MockData())
    my_task.training_indices = [0, 1, 2, 3]

    X_train = my_task.X_train
    y_train = my_task.y_train

    assert(X_train.shape == (4, 2))
    assert(np.all(X_train == np.array([[1, 2], [2, 3], [3, 4], [4, 5]])))
    assert(y_train.shape == (4, ))
    assert(np.all(y_train == np.array([10, 11, 12, 13])))

    my_task.test_indices = [0, 1, 2]

    X_test = my_task.X_test

    assert(X_test.shape == (3, 2))
    assert(np.all(X_test == np.array([[1, 2], [2, 3], [3, 4]])))

    my_task.validation_indices = [6, 7, 8]

    X_val = my_task.X_val
   
    assert(X_val.shape == (3, 2))
    assert(np.all(X_val == np.array([[7, 8], [8, 9], [9, 10]])))