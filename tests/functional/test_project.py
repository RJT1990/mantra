# Test making a new project

import subprocess
import os
import shutil

def test_mantraml():
    out = subprocess.run(["mantra"])

    assert out.returncode == 0

def test_project():
    cwd = os.getcwd()
    assert cwd.endswith("tests")

    basedir = cwd.replace("/mantraml/tests", "")

    proj_name = "my_project"
    model_name = "my_new_model"
    data_name = "my_new_data"

    proj_dir = os.path.join(basedir, proj_name)

    # delete any old projects if they are present
    if os.path.isdir(proj_dir):
        shutil.rmtree(proj_dir)

    out = subprocess.run(["mantra", "launch", proj_name], cwd=basedir)
    assert out.returncode == 0

    out = subprocess.run(["mantra", "makemodel", model_name], cwd=proj_dir)
    assert out.returncode == 0
    assert os.path.isdir(os.path.join(proj_dir, "models", model_name))

    out = subprocess.run(["mantra", "makedata", data_name], cwd=proj_dir)
    assert out.returncode == 0
    assert os.path.isdir(os.path.join(proj_dir, "data", data_name))


