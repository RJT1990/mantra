import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import os

from .Dataset import Dataset


class TabularDataset(Dataset):
    """
    This class implements dataset processing methods for a tabular dataset
    """

    # These class variables contain metadata on the Dataset
    dataset_type = 'tabular' # optional labelling of the datatype for free methods - see mantraml docs

    def __init__(self, target, features, target_index, features_index, **kwargs):       
        """
        This initialises an instance of the Dataset

        Parameters
        -----------

        target - str
            The name of the label column (e.g.'my_labels'); optionally None if you refer to the column index instead (target_index)

        features - list of strs
            The names of the feature columns (e.g.['feature_1', 'feature_2']); optionally None if you refer to the feature indices instead (features_index)

        target_index - int
            The index of the label column (e.g. 0); optionally None if you refer to the column names instead (target)

        features_index - list of ints
            The indices of the feature columns (e.g.[1, 2]); optionally None if you refer to the feature names instead (features)            
        """

        # metadata
        self.name = inspect.getfile(self.__class__).split('/')[-2]

        # tabular data
        self.data_file = data_file
        self.target = target
        self.features = features
        self.target_index = target_index
        self.features_index = features_index

        # df extraction
        self.data_from_files = False
        self.data_outside_project = False

        if self.files is not None:
            self.data_from_files = True

            self.outside_project = False
            self.extract_file_dict = {}

            for file in self.files:
                if '/' in file:
                    self.data_outside_project = True
                    self.data_dir = '%s/.tempmantra/' % os.getcwd()
                else:
                    self.data_outside_project = False
                    self.data_dir = '%s/data/%s/' % (os.getcwd(), self.folder_name)

                if '.tar.gz' in file:
                    self.extract_file_dict[file] = True
                else:
                    self.extract_file_dict[file] = False

        # configure and extract from tar
        self.configure_data(**kwargs)
        self.extract_data()

        # define the core DataFrames
        file_type = self.data_file.split('.')[-1] 
        if file_type == 'csv':
            df = pd.read_csv('%s/%s' % ('%s%s' % (self.data_dir, 'raw/.extract'), self.data_file))
        else:
            raise TypeError('The file type .%s is unsupported' % file_type)

        self.df_train = df.iloc[:int(df.shape[0]*self.training_test_split), :]
        self.df_test = df.iloc[int(df.shape[0]*0.75):, :]

        # Training and test data
        self.X = self.extract_inputs(training=True)
        self.y = self.extract_outputs(training=True)
        self.X_test = self.extract_inputs(training=False)
        self.y_test = self.extract_outputs(training=False)

    def extract_inputs(self, training=True):
        """
        This method extracts inputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Parameters
        --------
        training - bool
            If True, returns training data, else test data

        Returns
        --------
        np.ndarray - of data inputs (X vector)
        """

        if training:
            df = self.df_train
        else:
            df = self.df_test

        if self.features:
            return df[self.features].values

        if self.features_index:
            return df[:, self.features_index].values

    def extract_outputs(self, training=True):
        """
        This method extracts outputs from the data. The output should be an np.ndarray that can be processed 
        by the model.

        Parameters
        --------
        training - bool
            If True, returns training data, else test data

        Returns
        --------
        np.ndarray - of data inputs (y vector)
        """

        if training:
            df = self.df_train
        else:
            df = self.df_test

        if self.features:
            return df[self.target].values

        if self.features_index:
            return df.iloc[:, self.target_index].values