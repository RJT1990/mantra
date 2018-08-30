import copy
import os
import shutil
import runpy
import subprocess

from termcolor import colored

import mantraml
import argparse

from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml.core.cloud.AWS import AWS

from .consts import CONFIG_VARIABLES

CLOUD_PROVIDERS = ['aws']


class CloudCmd(BaseCommand):
    def add_arguments(self, parser):
        return parser

    def handle(self, args, unknown):
        """
        Trains a machine learning model with Mantra
        """
        print(colored('\n \033[1m Mantra Cloud Configuration', 'blue') + colored('\033[1m ☁\n', 'green'))

        use_cloud = input(colored("\n \033[1m We will configure your Mantra project with cloud support. Continue? (y/n)\n\n", 'green'))

        if use_cloud != "y":
            exit()

        cloud_provider = None

        while cloud_provider not in CLOUD_PROVIDERS:
            cloud_provider = input(colored("\n \033[1m Which cloud provider would you like to use? E.g. aws \n\n", 'green'))

            if cloud_provider not in CLOUD_PROVIDERS:
                print(colored('\n \033[1m Invalid cloud provider. Please choose one of the available options.\n', 'red'))

        if cloud_provider == 'aws':
            aws_access_key_id = input(colored("\n \033[1m What is your AWS Access Key Id? e.g. AKIAIL22SZKS2NO4GAOQ \n\n", 'green'))
            aws_secret_access_key = input(colored("\n \033[1m What is your AWS Secret Access Key? e.g. AFEF4FH34aIfdoRaFAnw21ATp5hSNwsSFOs2cg/a \n\n", 'green')) 
            aws_key_path = input(colored("\n \033[1m What is your AWS Key Path? e.g. ~/.ssh/mykey.pem \n\n", 'green')) 
            is_security_group = input(colored("\n \033[1m Would you like to use a custom security group? (If not will use default) y/n? \n\n", 'green')) 

            if is_security_group == "y":
                aws_security_group = input(colored("\n \033[1m What is the name of the security group? e.g. mantrasg \n\n", 'green')) 
                aws_security_group = "'%s'" % aws_security_group
            else:
                aws_security_group = None

            print(colored('\n \033[1m Ensure that your security group has the right inbound/outbound permissions, and ability to create instances. \n', 'white'))

            aws_default_region = input(colored("\n \033[1m Please choose your default AWS region. E.g. us-east-1 \n\n", 'green')) 
            aws_default_s3_region = input(colored("\n \033[1m Please choose your default S3 region. E.g. us-east-1 \n\n", 'green')) 

            settings_path = "%s/settings.py" % os.getcwd()
            settings_content = open(settings_path, 'r')
            new_lines = []

            for line in settings_content:

                if not any([config_var in line for config_var in CONFIG_VARIABLES + ['CLOUD CONFIGURATION SETTINGS']]):
                    new_lines.append(line)

            new_lines.append('\n# CLOUD CONFIGURATION SETTINGS\n')
            new_lines.append("CLOUD_PROVIDER = 'AWS'\n")
            new_lines.append("AWS_KEY_PATH = '%s'\n" % aws_key_path)
            new_lines.append("AWS_SECURITY_GROUP = %s\n" % aws_security_group)
            new_lines.append("S3_AVAILABILITY_ZONE = '%s'\n" % aws_default_s3_region)
            new_lines.append("AWS_ACCESS_KEY_ID = '%s'\n" % aws_access_key_id)
            new_lines.append("AWS_SECRET_ACCESS_KEY = '%s'\n" % aws_secret_access_key)
            new_lines.append("AWS_DEFAULT_REGION = '%s'" % aws_default_region)

            with open(settings_path, "w") as settings_file:
                settings_file.write(''.join(new_lines))

            credentials_file = '[default]\naws_access_key_id = %s\naws_secret_access_key = %s' % (aws_access_key_id, aws_secret_access_key)
            config_file = '[default]\nregion=%s' % (aws_default_region)
            credentials_path = os.path.expanduser("~/.aws/credentials")
            config_path = os.path.expanduser("~/.aws/config")

            with open(credentials_path, "w") as credentials:
                credentials.write(credentials_file)

            with open(config_path, "w") as config:
                config.write(config_file)

            print(colored("\n \033[1m Great, that's all set up. Make sure you have the AWS CLI installed as a dependency.\n\n", 'blue'))


class Dict2Obj:
    def __init__(self, **entries):
        self.__dict__.update(entries)












