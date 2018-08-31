import os
import numpy as np
import pandas as pd
import yaml

from mantraml.core.cloud.AWS import AWS
import pytest


class AWSNoInit(AWS):
    """
    So we don't have to spin up actual instances etc...
    """
    def __init__(self):
        self.model_hash = 'model_hash'
        self.data_hash = 'data_hash'
        self.task_hash = 'task_hash'
        self.project_name = 'my_project'
        self.trial_folder_name = 'my_trial_folder'
        self.public_dns = 'dns_address.cloudprovider.com'


def test_export_trials_to_s3():

    class Settings:
        S3_BUCKET_NAME = 'my_s3_bucket'

    class MockModel:
        trial_folder_name = 'my_trial_folder'
        settings = Settings()

    model = MockModel()
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

def test_configure_arguments():

    class MockArgParser:

        def __init__(self):
            self.__dict__ = {'dropout': 0.5, 'cloud': True, 'epochs': 10}

    args = MockArgParser()
    arg_str, arg_dict = AWS.configure_arguments(args)

    # cloud should not be parsed (not an additional argument to put in the cloud execution script)
    assert(arg_str == ' --dropout 0.5 --epochs 10' or arg_str == ' --epochs 10 --dropout 0.5') 

    assert('dropout' in arg_dict)
    assert('epochs' in arg_dict)
    assert(arg_dict['dropout'] == 0.5)
    assert(arg_dict['epochs'] == 10)

    arg_str, arg_dict = AWS.configure_arguments(args, **{'alpha': 0.1})

    # cloud should not be parsed (not an additional argument to put in the cloud execution script)
    assert(arg_str == ' --dropout 0.5 --epochs 10 --alpha 0.1' or arg_str == ' --epochs 10 --dropout 0.5 --alpha 0.1') 

    assert('dropout' in arg_dict)
    assert('epochs' in arg_dict)
    assert('alpha' in arg_dict)
    assert(arg_dict['dropout'] == 0.5)
    assert(arg_dict['epochs'] == 10)
    assert(arg_dict['alpha'] == 0.1)

    arg_str, arg_dict = AWS.configure_arguments(args, **{'cloud-extra': True})

    # cloud should not be parsed (not an additional argument to put in the cloud execution script)
    assert(arg_str == ' --dropout 0.5 --epochs 10 --cloud-extra' or arg_str == ' --epochs 10 --dropout 0.5 --cloud-extra') 

    assert('dropout' in arg_dict)
    assert('epochs' in arg_dict)
    assert('cloud-extra' in arg_dict)
    assert(arg_dict['dropout'] == 0.5)
    assert(arg_dict['epochs'] == 10)
    assert(arg_dict['cloud-extra'] is True)

def test_configure_trial_metadata():

    class MockArgParser:

        def __init__(self):
            self.model_name = 'my_model'
            self.dataset = 'my_dataset'
            self.task = 'my_task'

    arg_dict = {'epochs': 20, 'savebestonly': True, 'dropout': 0.5}
    args = MockArgParser()
    aws_instance = AWSNoInit()
    yaml_contents, log_contents = aws_instance.configure_trial_metadata(args=args, arg_dict=arg_dict, execute=False)
    log_contents = log_contents.split(" ")

    # check that everything is stored correctly in the log
    assert(len(log_contents) == 10)
    assert(len(log_contents[0]) == 10) # the timestamp
    assert(int(log_contents[0]) > 1535000000) # sanity check of timestamp
    assert(len(log_contents[2]) == 64) # SHA-256 hash for the trial is 64 length
    assert(len(log_contents[3]) == 64) # SHA-256 hash for the trial group is 64 length
    assert(log_contents[4] == args.model_name) # Model name
    assert(log_contents[5] == aws_instance.model_hash) # Model hash
    assert(log_contents[6] == args.dataset) # Data name
    assert(log_contents[7] == aws_instance.data_hash) # Data hash
    assert(log_contents[8] == args.task) # Task name
    assert(log_contents[9] == aws_instance.task_hash + '\n') # Task hash
    assert(log_contents[1] == '%s_%s_%s_%s' % (log_contents[0], args.model_name, args.dataset, log_contents[2][:6]))

    yaml_contents = yaml.load(yaml_contents)

    assert(yaml_contents['model_hash'] == aws_instance.model_hash)
    assert(yaml_contents['task_hash'] == aws_instance.task_hash)
    assert(yaml_contents['task_name'] == args.task)
    assert(yaml_contents['data_name'] == args.dataset)
    assert(yaml_contents['data_hash'] == aws_instance.data_hash)
    assert(yaml_contents['savebestonly'] == True)
    assert(yaml_contents['timestamp'] == int(log_contents[0]))
    assert(yaml_contents['trial_group_hash'] == log_contents[3])
    assert(yaml_contents['model_name'] == args.model_name)
    assert(yaml_contents['trial_hash'] == log_contents[2])

    args.task = None

    yaml_contents, log_contents = aws_instance.configure_trial_metadata(args=args, arg_dict=arg_dict, execute=False)
    log_contents = log_contents.split(" ")

    # check that everything is stored correctly in the log
    assert(len(log_contents) == 10)
    assert(len(log_contents[0]) == 10) # the timestamp
    assert(int(log_contents[0]) > 1535000000) # sanity check of timestamp
    assert(len(log_contents[2]) == 64) # SHA-256 hash for the trial is 64 length
    assert(len(log_contents[3]) == 64) # SHA-256 hash for the trial group is 64 length
    assert(log_contents[4] == args.model_name) # Model name
    assert(log_contents[5] == aws_instance.model_hash) # Model hash
    assert(log_contents[6] == args.dataset) # Data name
    assert(log_contents[7] == aws_instance.data_hash) # Data hash
    assert(log_contents[8] == 'none') # Task name
    assert(log_contents[9] == 'none\n') # Task hash
    assert(log_contents[1] == '%s_%s_%s_%s' % (log_contents[0], args.model_name, args.dataset, log_contents[2][:6]))

    yaml_contents = yaml.load(yaml_contents)

    assert(yaml_contents['model_hash'] == aws_instance.model_hash)
    assert(yaml_contents['task_hash'] == 'none')
    assert(yaml_contents['task_name'] == 'none')
    assert(yaml_contents['data_name'] == args.dataset)
    assert(yaml_contents['data_hash'] == aws_instance.data_hash)
    assert(yaml_contents['savebestonly'] == True)
    assert(yaml_contents['timestamp'] == int(log_contents[0]))
    assert(yaml_contents['trial_group_hash'] == log_contents[3])
    assert(yaml_contents['model_name'] == args.model_name)
    assert(yaml_contents['trial_hash'] == log_contents[2])

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
    assert('mantra train my_model --dataset my_dataset --task my_task --dropout 0.5 --epochs 10 --savebestonly' in sh_script_lines[4].replace("  ", ""))

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