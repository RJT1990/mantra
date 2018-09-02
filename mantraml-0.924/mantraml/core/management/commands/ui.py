import os
import shutil
import uuid
import subprocess
import mantraml
from mantraml.core.management.commands.BaseCommand import BaseCommand


class UICmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("project_path", default=".", type=str, nargs="?")
        return parser

    def handle(self, args, unknown):
        path = args.project_path
        path = os.path.abspath(path)
        project_root = None

        # check if the path is to an mantra.yml file or contains it
        if path.endswith("mantra.yml"):
            project_root = os.path.dirname(path)
        else:
            if os.path.isfile(os.path.join(path, "mantra.yml")):
                project_root = path

        # run the Django server if we found the project root
        if project_root:
            cmd = ["python", "manage.py", "runserver"]
            os.environ["MANTRA_PROJECT_ROOT"] = project_root
            cwd = os.path.join(os.path.dirname(mantraml.__file__), "ui")
            subprocess.run(cmd, cwd=cwd)
        else:
            if path == os.path.abspath("."):
                print("ERROR: Cannot find mantra.yml in the current directory")
            else:
                print("ERROR: Path '%s' does not contain an mantra project" % path)
