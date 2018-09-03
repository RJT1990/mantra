import os
import numpy as np
import pandas as pd
import yaml

from mantraml.core.training.Trial import Trial

import pytest


def test_configure_arguments():

    class MockArgParser:

        def __init__(self):
            self.__dict__ = {'name': None, 'dropout': 0.5, 'cloud': True, 'epochs': 10}

    args = MockArgParser()
    arg_str, arg_dict = Trial.configure_arguments(args)

    # cloud should not be parsed (not an additional argument to put in the cloud execution script)
    assert(arg_str == ' --dropout 0.5 --epochs 10' or arg_str == ' --epochs 10 --dropout 0.5') 

    assert('dropout' in arg_dict)
    assert('epochs' in arg_dict)
    assert(arg_dict['dropout'] == 0.5)
    assert(arg_dict['epochs'] == 10)

    arg_str, arg_dict = Trial.configure_arguments(args, **{'alpha': 0.1})

    # cloud should not be parsed (not an additional argument to put in the cloud execution script)
    assert(arg_str == ' --dropout 0.5 --epochs 10 --alpha 0.1' or arg_str == ' --epochs 10 --dropout 0.5 --alpha 0.1') 

    assert('dropout' in arg_dict)
    assert('epochs' in arg_dict)
    assert('alpha' in arg_dict)
    assert(arg_dict['dropout'] == 0.5)
    assert(arg_dict['epochs'] == 10)
    assert(arg_dict['alpha'] == 0.1)

    arg_str, arg_dict = Trial.configure_arguments(args, **{'cloud-extra': True})

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
            self.name = None
            
    args = MockArgParser()
    args.savebestonly = True
    args.epochs = 20
    args.dropout = 0.5

    trial = Trial(project_name="my_project", 
        model_name="my_model", 
        dataset_name=args.dataset, 
        task_name=args.task, 
        cloud=False, 
        args=args)

    trial.model_hash = "model_hash"
    trial.data_hash = "data_hash"
    trial.task_hash = "task_hash"

    trial.configure_trial_metadata()
    yaml_contents = trial.yaml_content
    log_contents = trial.log_file_contents

    log_contents = log_contents.split(" ")

    # check that everything is stored correctly in the log
    assert(len(log_contents) == 10)
    assert(len(log_contents[0]) == 10) # the timestamp
    assert(int(log_contents[0]) > 1535000000) # sanity check of timestamp
    assert(len(log_contents[2]) == 64) # SHA-256 hash for the trial is 64 length
    assert(len(log_contents[3]) == 64) # SHA-256 hash for the trial group is 64 length
    assert(log_contents[4] == trial.model_name) # Model name
    assert(log_contents[5] == trial.model_hash) # Model hash
    assert(log_contents[6] == trial.dataset_name) # Data name
    assert(log_contents[7] == trial.data_hash) # Data hash
    assert(log_contents[8] == trial.task_name) # Task name
    assert(log_contents[9] == trial.task_hash + '\n') # Task hash
    assert(log_contents[1] == '%s_%s_%s_%s' % (log_contents[0], args.model_name, args.dataset, log_contents[2][:6]))

    yaml_contents = yaml.load(yaml_contents)

    assert(yaml_contents['model_hash'] == trial.model_hash)
    assert(yaml_contents['task_hash'] == trial.task_hash)
    assert(yaml_contents['task_name'] == trial.task_name)
    assert(yaml_contents['data_name'] == trial.dataset_name)
    assert(yaml_contents['data_hash'] == trial.data_hash)
    assert(yaml_contents['savebestonly'] is True)
    assert(yaml_contents['timestamp'] == int(log_contents[0]))
    assert(yaml_contents['trial_group_hash'] == log_contents[3])
    assert(yaml_contents['model_name'] == trial.model_name)
    assert(yaml_contents['trial_hash'] == log_contents[2])

    trial.task_name = None

    trial.configure_trial_metadata()
    yaml_contents = trial.yaml_content
    log_contents = trial.log_file_contents
    log_contents = log_contents.split(" ")

    # check that everything is stored correctly in the log
    assert(len(log_contents) == 10)
    assert(len(log_contents[0]) == 10) # the timestamp
    assert(int(log_contents[0]) > 1535000000) # sanity check of timestamp
    assert(len(log_contents[2]) == 64) # SHA-256 hash for the trial is 64 length
    assert(len(log_contents[3]) == 64) # SHA-256 hash for the trial group is 64 length
    assert(log_contents[4] == trial.model_name) # Model name
    assert(log_contents[5] == trial.model_hash) # Model hash
    assert(log_contents[6] == trial.dataset_name) # Data name
    assert(log_contents[7] == trial.data_hash) # Data hash
    assert(log_contents[8] == 'none') # Task name
    assert(log_contents[9] == 'none\n') # Task hash
    assert(log_contents[1] == '%s_%s_%s_%s' % (log_contents[0], args.model_name, args.dataset, log_contents[2][:6]))

    yaml_contents = yaml.load(yaml_contents)

    assert(yaml_contents['model_hash'] == trial.model_hash)
    assert(yaml_contents['task_hash'] == 'none')
    assert(yaml_contents['task_name'] == 'none')
    assert(yaml_contents['data_name'] == trial.dataset_name)
    assert(yaml_contents['data_hash'] == trial.data_hash)
    assert(yaml_contents['savebestonly'] == True)
    assert(yaml_contents['timestamp'] == int(log_contents[0]))
    assert(yaml_contents['trial_group_hash'] == log_contents[3])
    assert(yaml_contents['model_name'] == trial.model_name)
    assert(yaml_contents['trial_hash'] == log_contents[2])