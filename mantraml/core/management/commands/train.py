import copy
import os
import shutil
import uuid
import runpy
import subprocess
import mantraml

import argparse

from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.management.commands.utils import artefacts_create_folder
from mantraml.core.training.Train import Train

class TrainCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--cloud', action="store_true", help="Trains your model with your cloud provider")
        parser.add_argument('--dev', action="store_true", help="Trains your model on a development instance")
        parser.add_argument('--savebestonly', action="store_true", help="Only saves model weights when better evaluation score is achieved")
        parser.add_argument('--verbose', action="store_true", help="Verbose printing")
        parser.add_argument('--cloudremote', action="store_true", help="Used on cloud instances; user should not have to use this argument")
        parser.add_argument('-n', '--name', type=str, help="Optional name for your trial group, e.g. 'Dropout Trials'")

        parser.add_argument('--config')
        parser.add_argument('--dataset', type=str, required=True, help="The folder name of your dataset, e.g. cifar_10")
        parser.add_argument('--instance-ids', nargs="+", help="A list of instance_ids, e.g. i-f4f42g42g i-fefefwfwew")
        parser.add_argument('--features', nargs="+", help="A list of feature column names; used for tabular datasets")
        parser.add_argument('--target', type=str, required=False, help="A string representing the target name for tabular datasets")
        parser.add_argument('--feature-indices', nargs="+", help="A list of feature column indices; used for tabular datasets")
        parser.add_argument('--target-index', type=int, required=False, help="A string representing the target index for tabular datasets")
        # training arguments
        parser.add_argument('--task', type=str, required=False, help="The folder name of your task, e.g. classify_images")
        parser.add_argument('--batch-size', type=int, required=False, help="The batch size for training, e.g. 64")
        parser.add_argument('--epochs', type=int, required=False, help="The number of epochs during training")

        parser.add_argument('model_name', type=str, help="The folder name of your model, e.g. resnet")

        return parser

    @staticmethod
    def parse_unknown(unknown):
        """
        Input is a ArgumentParser.parse_known_args unknown argument output. We take the list and convert it into a dictionary
        linking the arguments to values.

        Parameters
        -----------
        unknown - list
            List of unknown arguments from an ArgumentParser.parse_known_args
            Example ['--dropout-value', 0.5, '--use-this-feature']

        Returns
        -----------
        dict - linking command line arguments with values; e.g. {'dropout_value': 0.5, 'use_this_feature': True}
        """

        extra_args = {}

        for value_no, value in enumerate(unknown):

            if value_no == 0:
                old_value = copy.deepcopy(value)
                continue

            if '--' in value and '--' in old_value:
                extra_args[old_value.replace('--', '').replace('-', '_')] = True
            elif '--' not in value and '--' in old_value:
                if value in ['True', 'False']:
                    extra_args[old_value.replace('--', '').replace('-', '_')] = bool(value)
                elif value == 'None':
                    extra_args[old_value.replace('--', '').replace('-', '_')] = None
                else:
                    extra_args[old_value.replace('--', '').replace('-', '_')] = value

            if '--' in value and value_no == len(unknown) - 1:
                extra_args[value.replace('--','').replace('-', '_')] = True
            
            old_value = copy.deepcopy(value)

        return extra_args

    def handle(self, args, unknown):
        """
        Trains a machine learning model using Mantra
        """

        settings = Dict2Obj(**runpy.run_path("%s/%s" % (os.getcwd(), 'settings.py')))
        project_name = os.getcwd().split('/')[-1]
        extra_args = self.parse_unknown(unknown)
        Train(project_name=project_name, settings=settings, args=args, **extra_args).begin()


class Dict2Obj:
    def __init__(self, **entries):
        self.__dict__.update(entries)