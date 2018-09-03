import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

from .Dataset import Dataset, cachedata


class TabularDataset(Dataset):
    """
    This class implements dataset processing methods for a tabular dataset
    """

    data_type = 'tabular'
    has_labels = True

    def __init__(self, **kwargs):       
        # Potential parameters to come through kwargs: target, features, target_index, features_index 
        # Or they can be hardcoded as class variables

        super().__init__(**kwargs)

        file_type = self.data_file.split('.')[-1] 
        if file_type == 'csv':
            self.df = pd.read_csv('%s/%s' % ('%s%s' % (self.data_dir, 'raw/.extract'), self.data_file))
        else:
            raise TypeError('The file type .%s is unsupported' % file_type)

    @cachedata
    def X(self):
        """
        This method extracts inputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs (X vector)
        """

        if self.features:
            return self.df[self.features].values

        if self.features_index:
            return self.df[:, self.features_index].values

    @cachedata
    def y(self):
        """
        This method extracts outputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Returns
        --------
        np.ndarray - of data inputs (y vector)
        """

        if self.features:
            return self.df[self.target].values

        if self.features_index:
            return self.df.iloc[:, self.target_index].values