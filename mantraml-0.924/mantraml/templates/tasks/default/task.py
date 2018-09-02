import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score

from mantraml.tasks.Task import Task


class MyTask(Task):
    task_name = 'My Example Task'
    evaluation_name = 'My Evaluation Metric'
    training_test_split = 0.75

    def evaluate(self, model):
        # Return an evaluation metric scalar here. For example, categorical cross entropy:
        # predictions = model.predict(model.X_test)
        # return -np.nansum(model.y_test*np.log(predictions) + (1-model.y_test)*np.log(1-predictions)) / predictions.shape[0]