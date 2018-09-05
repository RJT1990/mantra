import argparse

from mantraml.core.management.commands.cloud import CloudCmd
from mantraml.core.management.commands.importcmd import ImportCmd
from mantraml.core.management.commands.makedata import MakeDataCmd
from mantraml.core.management.commands.makemodel import MakeModelCmd
from mantraml.core.management.commands.maketask import MakeTaskCmd
from mantraml.core.management.commands.sync import SyncCmd
from mantraml.core.management.commands.testdata import TestDataCmd
from mantraml.core.management.commands.train import TrainCmd
from mantraml.core.management.commands.ui import UICmd
from mantraml.core.management.commands.launch import LaunchCmd

def cmd_line():
    """
    Parse the root command line

    :return:
    """

    parser = argparse.ArgumentParser(prog='mantra')

    # register all the subcommands here
    subcommands = {
        "cloud": CloudCmd(),
        "ui": UICmd(),
        "launch": LaunchCmd(),
        "makemodel": MakeModelCmd(),
        "makedata": MakeDataCmd(),
        "maketask": MakeTaskCmd(),
        "sync": SyncCmd(),
        "testdata": TestDataCmd(),
        "train": TrainCmd(),
        "import": ImportCmd(),
    }
    subparsers = parser.add_subparsers(help='sub-command help')

    # register all the subparsers
    for key,obj in subcommands.items():
        subparser = subparsers.add_parser(key, help="%s help" % key)
        subparser = obj.add_arguments(subparser)
        subparser.set_defaults(func=obj.handle)
        obj.parser = parser

    # parse the call the appropriate function
    args, unknown = parser.parse_known_args()

    if "func" in args:
        args.func(args, unknown)
    else:
        parser.print_help()

