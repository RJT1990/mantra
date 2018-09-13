import os
import shutil
import uuid
import subprocess
import mantraml
from mantraml.core.hashing.MantraHashed import MantraHashed
from mantraml.core.management.commands.BaseCommand import BaseCommand
import tempfile
from pathlib import Path
import sys
import getpass
import itertools
import requests
from urllib.parse import urljoin
import json

from mantraml.core.management.commands.importcmd import find_artefacts


class UploadCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument("artefacts", type=str, nargs="*")
        parser.add_argument("--remote", type=str, default="https://mantrahub.io")
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
            if Path("results").exists():
                all_results = [str(p) for p in Path("results").iterdir() if p.is_dir()]
            else:
                all_results = []
            all_artefacts = list(itertools.chain(all_models, all_datasets, all_tasks, all_results))

        else:
            all_artefacts = args.artefacts
            missing_artefacts = [a for a in all_artefacts if not Path(a).exists()]
            if len(missing_artefacts) > 0:
                print("ERROR: The following artefact(s) are missing: `%s`" % missing_artefacts)
                sys.exit(1)

        # TODO: Results will have dependencies, make sure those are taken into account

        # 1) Get the hashes for all the files and dependencies

        all_hashes = []
        for artefact_dir in all_artefacts:
            artefact_hash, file_hashes = MantraHashed.get_folder_hash(artefact_dir)
            all_hashes.append({
                "artefact_dir": artefact_dir,
                "artefact_hash": artefact_hash,
                "file_hashes": file_hashes,
            })

        # 2) Get the credentials

        # prompt for username and password
        mantrahub_user = input("Your mantrahub username: ")
        if mantrahub_user.strip() == "":
            print("ERROR: The username cannot be empty, quitting...")
            sys.exit(1)

        mantrahub_pass = getpass.getpass("Your mantrahub password: ")

        # 3) Send the request to the server to see which files need to be uploaded
        full_url = urljoin(args.remote,  "/api/artefacts_diff")
        json_payload = json.dumps({"all_hashes": all_hashes})
        diff_response = requests.post(full_url, json=json_payload, auth=(mantrahub_user, mantrahub_pass))

        diff = json.loads(diff_response.json())["diff_hashes"]

        if diff:
            upload_url_base = urljoin(args.remote, "api/upload_file/")
            for artefact in diff:
                for k,v in artefact["file_hashes"].items():
                    print("Uploading `%s`..." % v["path"])
                    files = {'file': open(v["path"], 'rb')}

                    h = {"Content-Disposition": "attachment; filename=%s" % v["path"]}
                    r = requests.put(upload_url_base+v["path"], files=files, headers=h,
                                     auth=(mantrahub_user, mantrahub_pass))


        # Finally, commit all the results
        print("Committing uploaded results...")
        commit_url = urljoin(args.remote, "api/artefacts_diff_commit")
        json_payload = json.dumps({"all_hashes": all_hashes, "diff_hashes": diff})
        commit_response = requests.post(commit_url, json=json_payload, auth=(mantrahub_user, mantrahub_pass))

        if commit_response.status_code == requests.codes.ok:
            print("SUCCESS: Upload successful.")
        else:
            print("ERROR: Commit not successful: %s" % commit_response.text)











