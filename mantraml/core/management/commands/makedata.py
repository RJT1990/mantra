import os
from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.management.commands.utils import artefacts_create_folder



class MakeDataCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--config', type=str)
        parser.add_argument('--template', type=str, required=False)
        parser.add_argument('--tar-path', type=str, required=False)
        parser.add_argument('--no-tar', dest='no_tar', action='store_true')

        # image data based commands
        parser.add_argument('--image-dim', type=int, nargs='+', required=False)
        parser.add_argument('--normalize', dest='normalize', action='store_true')

        # tabular data based commands
        parser.add_argument('--file-name', type=str, required=False)
        parser.add_argument('--target', type=str, required=False)
        parser.add_argument('--features', type=str, nargs='+', required=False)
        parser.add_argument('--target-index', type=int, required=False)
        parser.add_argument('--features-index', type=int, nargs='+', required=False)

        parser.add_argument('path', type=str)
        return parser

    def handle(self, args, unknown):
        """
        Creates a new artefact folder for a data package
        """
        artefacts_create_folder(prog_name="makedata", project_dir=os.getcwd(), args=args)
