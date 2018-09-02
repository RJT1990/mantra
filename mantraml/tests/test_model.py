import os
import numpy as np
import pandas as pd
import yaml

from mantraml.models import MantraModel

import pytest


def test_configure_core_arguments():

    class MockArgParser:

        def __init__(self):
            self.batch_size = 100
            self.epochs = 150
            self.savebestonly = True

    args = MockArgParser()
    model = MantraModel()
    model.configure_core_arguments(args)

    assert(model.batch_size == 100)
    assert(model.epochs == 150)
    assert(model.save_best_only is True)


def test_update_trial_metadata():

    class MockTask:

        def __init__(self):
            self.best_loss = 50
            self.latest_loss = 60
            self.secondary_metrics_values = {'accuracy': 0.60, 'rmse': 1.543}
            self.best_secondary_metrics_values = {'accuracy': 0.80, 'rmse': 1.032}
            self.secondary_metrics = ['accuracy', 'rmse']

    model = MantraModel()
    model.epochs = 100
    model.task = None

    new_yaml_content = model.update_trial_metadata({}, 99)
    assert(yaml.load(new_yaml_content)['training_finished'] is True)

    new_yaml_content = model.update_trial_metadata({}, 98)
    assert(yaml.load(new_yaml_content)['training_finished'] is False)

    new_yaml_content = model.update_trial_metadata({}, 48)
    assert(yaml.load(new_yaml_content)['current_epoch'] == 49)

    model.task = MockTask()

    model.save_best_only = False
    new_yaml_content = model.update_trial_metadata({}, 98)
    assert(yaml.load(new_yaml_content)['validation_loss'] == model.task.latest_loss)
    assert(yaml.load(new_yaml_content)['secondary_metrics']['accuracy'] == 0.60)
    assert(yaml.load(new_yaml_content)['secondary_metrics']['rmse'] == 1.543)

    model.save_best_only = True
    new_yaml_content = model.update_trial_metadata({}, 98)
    assert(yaml.load(new_yaml_content)['validation_loss'] == model.task.best_loss)
    assert(yaml.load(new_yaml_content)['secondary_metrics']['accuracy'] == 0.80)
    assert(yaml.load(new_yaml_content)['secondary_metrics']['rmse'] == 1.032)







