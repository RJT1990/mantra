import os
from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.management.commands.utils import artefacts_create_folder


class MakeTaskCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--config', type=str)
        parser.add_argument('--template', type=str, required=False)
        parser.add_argument('path', type=str)
        return parser

    def handle(self, args, unknown):
        """
        Creates a new artefact folder for a task package
        """
        artefacts_create_folder(prog_name="maketask", project_dir=os.getcwd(), args=args)
