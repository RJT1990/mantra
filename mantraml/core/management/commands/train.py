import copy
import os
import shutil
import uuid
import runpy
import subprocess
import mantraml

import argparse

from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.management.commands.utils import artefacts_create_folder, train_model


class TrainCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--cloud', action="store_true")
        parser.add_argument('--dev', action="store_true")
        parser.add_argument('--savebestonly', action="store_true")
        parser.add_argument('--verbose', action="store_true")
        parser.add_argument('--config')
        parser.add_argument('--dataset', type=str, required=True)
        parser.add_argument('--instance-ids', nargs="+")

        # training arguments
        parser.add_argument('--task', type=str, required=False)
        parser.add_argument('--batch-size', type=int, required=False)
        parser.add_argument('--epochs', type=int, required=False)

        parser.add_argument('model_name', type=str)

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
        train_model(project_name=project_name, settings=settings, args=args, **extra_args)


class Dict2Obj:
    def __init__(self, **entries):
        self.__dict__.update(entries)