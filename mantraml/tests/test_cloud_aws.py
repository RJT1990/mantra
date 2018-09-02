import os
import numpy as np
import pandas as pd
import yaml

from mantraml.core.cloud.AWS import AWS
from mantraml.core.training.Trial import Trial

import pytest

class TrialMock:

    def __init__(self):
        self.trial_folder_name = 'my_trial_folder'


class AWSNoInit(AWS):
    """
    So we don't have to spin up actual instances etc...
    """
    def __init__(self):
        self.model_hash = 'model_hash'
        self.data_hash = 'data_hash'
        self.task_hash = 'task_hash'
        self.project_name = 'my_project'
        self.trial = TrialMock()
        self.public_dns = 'dns_address.cloudprovider.com'
        self.framework = 'none'


def test_export_trials_to_s3():

    class Settings:
        S3_BUCKET_NAME = 'my_s3_bucket'

    class MockModel:
        trial_folder_name = 'my_trial_folder'
        settings = Settings()

    model = MockModel()
    model.trial = TrialMock()
    aws_cmd = AWS.export_trials_to_s3(model=model, execute=False)

    predicted_path = '%s/trials/%s/' % (os.getcwd(), model.trial_folder_name)

    assert(aws_cmd == 'aws s3 --exact-timestamps sync --quiet %s s3://my_s3_bucket/trials/my_trial_folder/' % predicted_path)

def test_sync_data():

    class Settings:
        S3_BUCKET_NAME = 'my_s3_bucket'

    class MockModel:
        trial_folder_name = 'my_trial_folder'
        settings = Settings()

    class MockArgParser:

        def __init__(self, artefact):
            self.artefact = artefact

    args_trials = MockArgParser('trials')
    args_data = MockArgParser('data')
    args_other = MockArgParser('other')

    model = MockModel()
    settings = Settings()
    
    aws_cmd_trials = AWS.sync_data(args=args_trials, settings=settings, execute=False)
    aws_cmd_data = AWS.sync_data(args=args_data, settings=settings, execute=False)
    aws_cmd_other = AWS.sync_data(args=args_other, settings=settings, execute=False)

    assert(aws_cmd_trials == 'aws s3 --exact-timestamps sync s3://my_s3_bucket/trials trials')
    assert(aws_cmd_data == 'aws s3 --exact-timestamps sync s3://my_s3_bucket/data data')
    assert(aws_cmd_other is None)

def test_export_project_files_to_instances():

    class Settings:
        AWS_KEY_PATH = './ssh/mysupersecret.key'

    aws_instance = AWSNoInit()
    aws_instance.settings = Settings()
    rsync_string = aws_instance.export_project_files_to_instances(execute=False)

    exclude_string = "--exclude 'raw/*' --exclude 'trials/*' --exclude '.extract*' --exclude '.mantra*'"
    assert(rsync_string == "rsync -avL %s --progress -e 'ssh -i ./ssh/mysupersecret.key' ./ ubuntu@dns_address.cloudprovider.com:/home/ubuntu/my_project > /dev/null" % (exclude_string))

def test_get_training_data_from_s3():

    class Settings:
        AWS_KEY_PATH = './ssh/mysupersecret.key'
        S3_BUCKET_NAME = 'my_s3_bucket'

    aws_instance = AWSNoInit()
    aws_instance.settings = Settings()

    # no epoch in output
    output = 'Setting up Instance...'
    aws_cmd = aws_instance.get_training_data_from_s3(output=output, send_weights=False, force=False, execute=False)
    assert(aws_cmd is None)

    # epoch in output and send weights
    output = 'Epoch'
    aws_cmd = aws_instance.get_training_data_from_s3(output=output, send_weights=True, force=False, execute=False)
    assert(aws_cmd == 'aws s3 --quiet --exact-timestamps sync s3://my_s3_bucket/trials/my_trial_folder trials/my_trial_folder')
    
    # epoch in output and don't send weights
    output = 'Epoch'
    aws_cmd = aws_instance.get_training_data_from_s3(output=output, send_weights=False, force=False, execute=False)
    assert(aws_cmd == "aws s3 --quiet --exact-timestamps sync s3://my_s3_bucket/trials/my_trial_folder trials/my_trial_folder --exclude 'checkpoint/*'")

    # no epoch in output but force with weights
    output = 'Setting up Instance...'
    aws_cmd = aws_instance.get_training_data_from_s3(output=output, send_weights=True, force=True, execute=False)
    assert(aws_cmd == 'aws s3 --quiet --exact-timestamps sync s3://my_s3_bucket/trials/my_trial_folder trials/my_trial_folder')

def test_s3_to_servers():

    class Settings:
        AWS_KEY_PATH = './ssh/mysupersecret.key'
        S3_BUCKET_NAME = 'my_s3_bucket'

    class MockArgParser:

        def __init__(self):
            self.model_name = 'my_model'
            self.dataset = 'my_dataset'
            self.task = 'my_task'

    aws_instance = AWSNoInit()
    aws_instance.settings = Settings()
    args = MockArgParser()

    # no epoch in output
    s3_command = aws_instance.s3_to_servers(args=args, execute=False)
    data_dir = 'data/%s' % args.dataset

    assert(s3_command == "cd my_project; sudo aws s3 --exact-timestamps sync s3://my_s3_bucket/%s %s/" % (data_dir, data_dir))

def test_send_sh_file_to_instances():

    class MockArgParser:

        def __init__(self):
            self.model_name = 'my_model'
            self.dataset = 'my_dataset'
            self.task = 'my_task'
            self.verbose = False

    aws_instance = AWSNoInit()
    args = MockArgParser()
    arg_str = '--dropout 0.5 --epochs 10 --savebestonly'

    # no epoch in output
    sh_script = aws_instance.send_sh_file_to_instances(args=args, arg_str=arg_str, execute=False)
    sh_script_lines = sh_script.split('\n')

    assert(sh_script_lines[0] == '#!/bin/bash')
    assert('source /home/ubuntu/anaconda3/bin/activate tensorflow_p36' in sh_script_lines[1].replace("  ", ""))
    assert('pip install -r requirements.txt --quiet --upgrade' in sh_script_lines[2].replace("  ", ""))
    assert('pip install mantraml --quiet' in sh_script_lines[3].replace("  ", ""))
    assert('mantra train my_model --dataset my_dataset --task my_task --cloudremote --dropout 0.5 --epochs 10 --savebestonly' in sh_script_lines[4].replace("  ", ""))

def test_setup_aws_credentials():

    class Settings:
        AWS_ACCESS_KEY_ID = 'key_id'
        AWS_SECRET_ACCESS_KEY = 'access_key'
        AWS_DEFAULT_REGION = 'us-east-1'

    aws_instance = AWSNoInit()
    aws_instance.settings = Settings()

    # no epoch in output
    credentials_file, config_file = aws_instance.setup_aws_credentials(execute=False)
    
    assert(credentials_file == '[default]\naws_access_key_id = key_id\naws_secret_access_key = access_key')
    assert(config_file == '[default]\nregion=us-east-1')