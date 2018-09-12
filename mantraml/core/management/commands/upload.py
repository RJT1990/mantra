import os
import shutil
import uuid
import subprocess
import mantraml
from mantraml.core.management.commands.BaseCommand import BaseCommand
import tempfile
from pathlib import Path
import sys
import getpass

from mantraml.core.management.commands.importcmd import find_artefacts


class UploadCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("artefacts", type=str, nargs="*")
        return parser

    def handle(self, args, unknown):
        if not Path("mantra.yml").exists():
            print("ERROR: Please run this command from your mantra project directory (i.e. the directory containing `mantra.yml`)")
            sys.exit(1)

        # collect the artefacts to upload
        if len(args.artefacts) == 0:
            # get all the datasets, models and results
            print("Uploading all datasets, models, tasks and results...")

            all_models = find_artefacts("", "models", "model.py")
            all_datasets = find_artefacts("", "data", "data.py")
            all_tasks = find_artefacts("", "tasks", "task.py")
            all_results = [str(p) for p in Path("results").iterdir() if p.is_dir()]

        else:
            all_models = [a for a in args.artefacts if a.startswith("models/")]
            all_datasets = [a for a in args.artefacts if a.startswith("data/")]
            all_tasks = [a for a in args.artefacts if a.startswith("tasks/")]
            all_results = [a for a in args.artefacts if a.startswith("results/")]

        # TODO: Results will have dependencies, make sure those are taken into account

        # prompt for username and password
        mantrahub_user = input("Your mantrahub username: ")
        if mantrahub_user.strip() == "":
            print("ERROR: The username cannot be empty, quitting...")
            sys.exit(1)

        mantrahub_pass = getpass.getpass("Your mantrahub password: ")

        # Now upload all the artefacts

        # 1) Get the hashes for all the files and dependencies








