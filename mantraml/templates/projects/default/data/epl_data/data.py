import numpy as np

from mantraml.data import TabularDataset


class PremierLeagueDataset(TabularDataset):
    """
    This dataset contains historical English Premier League data, as well as some arbitrary features...

    You can choose a custom target from the command line, e.g. mantra train my_model --dataset epl_football_data --target my_target

    You can set defaults here below
    """
    data_name = 'Premier League Data'
    files = ['data.csv']
    data_file = 'data.csv'
    data_image = "default.jpeg"
    data_tags = ['football', 'epl']
    has_labels = True

    # defaults - can be overridden by a command line argument, e.g. --target my_target --features feature_4 feature_5 
    target = ['home_win'] # whether the home team won or not
    features = ['feature_1', 'feature_2', 'feature_3']