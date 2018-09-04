import numpy as np

from mantraml.data import Dataset, cachedata


class ExampleDataset(Dataset):
    data_name = 'My Example Dataset'
    data_tags = ['example', 'new']
    files = ['example_dataset.tar.gz']

    @cachedata
    def X(self):
        # This method should return an np.ndarray of features that can be processed by a model
        # Your data files will be in the folder self.extracted_data_path

        return

    @cachedata
    def y(self):
        # This method should return an np.ndarray of labels that can be processed by a model
        # Your data files will be in the folder self.extracted_data_path

        return