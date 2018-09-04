import numpy as np
import tensorflow as tf
from sklearn.metrics import accuracy_score

from mantraml.tasks import Task


class BinaryCrossEntropy(Task):
    """
    This class defines a task with binary cross entropy; with a 0.50/0.25/0.25 training/test split 
    """

    task_name = 'Classifier Evaluation'
    evaluation_name = 'Binary Crossentropy'
    training_split = (0.5, 0.25, 0.25)
    secondary_metrics = ['accuracy']

    def evaluate(self, model):
        predictions = model.predict(self.X_val)
        return -np.nansum(self.y_val*np.log(predictions) + (1-self.y_val)*np.log(1-predictions)) / predictions.shape[0]

    def accuracy(self, model):
        predictions = model.predict(self.X_val)
        predictions[predictions > 0.5] = 1
        predictions[predictions <= 0.5] = 0
        return accuracy_score(self.y_val, predictions)


