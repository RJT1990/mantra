import os
import numpy as np
import pandas as pd
import yaml

from mantraml.models import MantraModel
from mantraml.models.tensorflow.callbacks import EvaluateTask

import pytest


def test_evaluate_task():

    class MockTask:

        def __init__(self):
            self.evaluation_name = 'Magic Loss'
            self.secondary_metrics = ['at_a_loss']

        def evaluate(self, mantra_model):
            return 5.0

        def at_a_loss(self, mantra_model):
            return 10.0

    mantra_model = MantraModel()
    mantra_model.task = MockTask()

    evaluate_task = EvaluateTask(mantra_model=mantra_model)
    assert(mantra_model.task.latest_loss == 5.0)
    assert(mantra_model.task.secondary_metrics_values['at_a_loss'] == 10.0)