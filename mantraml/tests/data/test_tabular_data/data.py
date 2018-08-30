import numpy as np

from mantraml.data.TabularDataset import TabularDataset


class MyDataset(TabularDataset):

    # These class variables contain metadata on the Dataset
    name = 'test_tabular_data'
    tar_name = 'dataset' # e.g 'example_images' for 'example_images.tar.gz'
    data_type = 'tabular' # optional labelling of the datatype for free methods - see Mantra docs
    has_labels = True


    def __init__(self, name, file_name='dataset.csv', target='team_1_score', 
        features=['d_ability_1', 'd_ability_3', 'is_february'], target_index=None, 
        features_index=None, **kwargs):       
        """
        This initialises an instance of a TabularDataset

        Parameters
        -----------
        
        name - str
            The folder name for the dataset

        file_name - str
            The name of the data file in the tar file to load the DataFrame from

        target - str
            The name of the label column (e.g.'my_labels'); optionally None if you refer to the column index instead (target_index)

        features - list of strs
            The names of the feature columns (e.g.['feature_1', 'feature_2']); optionally None if you refer to the feature indices instead (features_index)

        target_index - int
            The index of the label column (e.g. 0); optionally None if you refer to the column names instead (target)

        features_index - list of ints
            The indices of the feature columns (e.g.[1, 2]); optionally None if you refer to the feature names instead (features) 

        """

        super().__init__(name=name, file_name=file_name, target=target, features=features, target_index=target_index, 
            features_index=features_index, **kwargs)