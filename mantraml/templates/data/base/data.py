import numpy as np

from mantraml.data.Dataset import Dataset, datamethod


class ExampleDataset(Dataset):
    dataset_name = 'My Example Dataset'
    dataset_tags = ['example', 'new']
    files = ['example_dataset.tar.gz']

    @datamethod
    def X(self):
        # This method should return an np.ndarray of features that can be processed by a model
        # Your data files will be in the folder self.extracted_data_path

        return

    @datamethod
    def y(self):
        # This method should return an np.ndarray of labels that can be processed by a model
        # Your data files will be in the folder self.extracted_data_path

        return