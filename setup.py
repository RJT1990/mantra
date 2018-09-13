from setuptools import setup

PACKAGE_NAME = "mantraml"
LICENSE = "Apache 2.0"
AUTHOR = "Ross Taylor and Robert Stojnic"
EMAIL = "rj-taylor@live.co.uk"
URL = "https://www.atlas.ml"
DESCRIPTION = "A high-level, rapid development framework for ML projects."


setup(
    name=PACKAGE_NAME,
    maintainer=AUTHOR,
    version='0.963',
    packages=[PACKAGE_NAME, 'mantraml.core', 'mantraml.core.cloud', 'mantraml.core.hashing', 'mantraml.core.management', 'mantraml.core.management.commands', 'mantraml.data', 'mantraml.models', 
    'mantraml.tasks', 'mantraml.tests'],
    include_package_data=True,
    license=LICENSE,
    description=DESCRIPTION,
    long_description=DESCRIPTION,
    url=URL,
    install_requires=['boto3', 'django', 'numpy', 'paramiko', 'pillow', 'lazy-import', 'scipy', 'matplotlib', 'pandas', 'termcolor', 'pyyaml', 'requests'],
    scripts=['mantraml/bin/mantra'],
)