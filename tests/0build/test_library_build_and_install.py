import os
import subprocess

def test_make_and_install_library():
    # make sure mantraml is not already installed
    subprocess.run(["pip", "uninstall", "-y", "mantraml"])

    cwd = os.getcwd()
    assert cwd.endswith("tests")

    basedir = cwd.replace("/tests", "")
    build = subprocess.run(["python3", "setup.py", "sdist", "bdist_wheel"], cwd=basedir)
    assert build.returncode == 0

    # check the dist folder is not empty
    dist_files = os.listdir(os.path.join(basedir, "dist"))
    assert len(dist_files) > 0

    # get the latest wheel file
    wheel_files = [f for f in dist_files if f.endswith(".whl")]

    assert len(wheel_files) > 0

    latest_wheel = sorted(wheel_files)[-1]

    # install the library
    install = subprocess.run(["pip", "install", os.path.join("dist", latest_wheel)], cwd=basedir)
    assert install.returncode == 0


