import importlib
import os
import sys

from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.data.Dataset import Dataset
from mantraml.data.ImageDataset import ImageDataset
from mantraml.data.TabularDataset import TabularDataset

from mantraml.data.finders import find_dataset_class


BASE_DATA_CLASSES = ['Dataset', 'TabularDataset', 'ImageDataset']


class TestDataCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('path', type=str)
        return parser

    def handle(self, args, unknown):
        """
        Tests a dataset object
        """

        dataset = None

        sys.path.append(os.getcwd())
        
        data_module = importlib.import_module("data.%s.data" % args.path)
        dataset_class = find_dataset_class(data_module)

        if not dataset_class:
            raise ImportError('Could not import a Dataset class (could not find it in the data directory - it should be in data.py)')
        else:
            dataset = dataset_class(name=args.path)

        dataset.test()
