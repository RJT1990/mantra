import copy
import os
import shutil
import runpy
import subprocess
from termcolor import colored

import mantraml


import argparse

from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.cloud.AWS import AWS

ARTEFACT_NAMES = ['data', 'trials']


class SyncCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('artefact', type=str)
        return parser

    def handle(self, args, unknown):
        """
        Trains a machine learning model using Mantra
        """

        settings = Dict2Obj(**runpy.run_path("%s/%s" % (os.getcwd(), 'settings.py')))

        if args.artefact in ARTEFACT_NAMES:
            print(colored('\n \033[1m Mantra S3 Sync', 'blue') + colored('\033[1m 💾\n', 'green'))
            AWS.sync_data(args=args, settings=settings)
        else:
            print(colored(' \033[1m [X]', 'red') + colored(' Did not recognise the artefact name %s. Should be one of: %s' % (args.artefact, ARTEFACT_NAMES), 'red'))


class Dict2Obj:
    def __init__(self, **entries):
        self.__dict__.update(entries)