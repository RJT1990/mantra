import os
import shutil
import uuid
import subprocess
from urllib.parse import urljoin
from urllib.request import urlretrieve

import mantraml
from mantraml.core.management.commands.BaseCommand import BaseCommand
import tempfile
from pathlib import Path
import sys
import requests
import json


def find_artefacts(base_dir:str, type="models", target_file="model.py", target_string="mantraml"):
    """
    Find a Mantra artefacts directory

    :param base_dir: Base directory to look at
    :param type: Can be `models`, `data`, `tasks`
    :param target_file: File use to identify the artefact
    :param target_string: which string should be in the target file
    :return:
    """

    base_path = Path(base_dir, type)

    all_artefacts = []

    if base_path.exists():
        subdirs = [p for p in base_path.iterdir() if p.is_dir()]

        while len(subdirs) > 0:
            subdir = subdirs.pop()
            subdir_files = [p for p in subdir.iterdir()]

            # found the target file in this subdir!
            if target_file in [p.name for p in subdir_files]:
                # second check to see if mantraml is actually used
                with open(str(Path(base_dir, subdir, target_file)), "r") as f:
                    file_contents = f.read()
                if target_string in file_contents:
                    all_artefacts.append(str(subdir))
            else:
                # go into further subdirs
                subdirs.extend([p for p in subdir.iterdir() if p.is_dir()])

    return all_artefacts



def copy_over(temp_dir, paths, artefact="model", dir="models"):
    """
    Copy over from the clone repo to the current project

    :param temp_dir:
    :param paths:
    :param artefact:
    :param dir:
    :return:
    """

    for path in paths:
        print("Importing %s %s" % (artefact, str(Path(path).resolve().relative_to(Path(temp_dir).resolve()))))
        dest_path = Path(dir, Path(path).name)
        if dest_path.exists():
            print("Skipping `%s` as it already exists" % str(dest_path))
        else:
            shutil.copytree(path, str(dest_path))


class ImportCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("repo_or_artefact", type=str, help="Github repository or Mantrahub artefact name", nargs="+")
        parser.add_argument("--remote", type=str, default="https://mantrahub.io")
        return parser

    def handle(self, args, unknown):

        if not Path("mantra.yml").exists():
            print("ERROR: Please run this command from your mantra project directory (i.e. the directory containing `mantra.yml`)")
            sys.exit(1)

        # clone the git repository and import everything
        base_dir = tempfile.mkdtemp()
        temp_dir = base_dir

        if "github.com" in args.repo_or_artefact[0]:
            print("Cloning the git repository...")
            subprocess.run(["git", "clone", "--depth", "1", args.repo_or_artefact[0]], cwd=base_dir)

            # the result should be a single path, with the name of the repo
            cloned_paths = [p.resolve() for p in Path(base_dir).iterdir()]

            if len(cloned_paths) == 1:
                base_dir = str(cloned_paths[0])
            else:
                print("ERROR: The temporary directory `%s` has more than one cloned item. Please delete other items and retry." % base_dir)
                sys.exit(1)
        else:
            # use mantrahub
            json_payload = json.dumps({"artefacts": args.repo_or_artefact})
            full_url = urljoin(args.remote, "/api/artefacts_download_list")
            r = requests.post(full_url, json=json_payload)

            artefact_files = json.loads(r.json())
            if artefact_files == {}:
                for a in args.repo_or_artefact:
                    print("ERROR: Artefact `%s` not found" % a)
            for k,v in artefact_files.items():
                if len(v) == 0:
                    print("ERROR: Artefact `%s` not found, skipping." % k)
                else:
                    print("Downloading `%s`..." % k)
                    for file in v:
                        dest_file = os.path.join(base_dir, file["path"])
                        Path(dest_file).parent.mkdir(parents=True, exist_ok=True)
                        urlretrieve(urljoin(args.remote, file["url_path"]), dest_file)

        all_models = find_artefacts(base_dir, "models", "model.py")
        all_datasets = find_artefacts(base_dir, "data", "data.py")
        all_tasks = find_artefacts(base_dir, "tasks", "task.py")
        all_results = find_artefacts(base_dir, "results", "result.yml", "name:")

        copy_over(temp_dir, all_models, "model", "models")
        copy_over(temp_dir, all_datasets, "dataset", "data")
        copy_over(temp_dir, all_tasks, "task", "tasks")
        copy_over(temp_dir, all_results, "result", "results")






