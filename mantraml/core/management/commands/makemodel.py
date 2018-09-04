import os
from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.management.commands.utils import artefacts_create_folder

class MakeModelCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--config', type=str)
        parser.add_argument('path', type=str)  # catch-all

        parser.add_argument('--template', type=str, required=False)

        return parser

    def handle(self, args, unknown):
        """
        Creates a new artefact folder for models
        """
        artefacts_create_folder(prog_name="makemodel", project_dir=os.getcwd(), args=args)
