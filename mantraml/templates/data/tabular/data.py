import numpy as np

from mantraml.data import TabularDataset


class MyTabularDataset(TabularDataset):

    data_name = 'Example Table Data'
    files = ['example_dataset.tar.gz']
    data_file = 'example_dataset.csv'
    data_tags = ['tabular']
    has_labels = True