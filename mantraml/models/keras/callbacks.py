import os
import tensorflow as tf


class EvaluateTask(tf.keras.callbacks.Callback):
    """
    Evaluates a model performance on a task according to the Mantra task object at end of epoch
    """

    def __init__(self, mantra_model):
        super(EvaluateTask, self).__init__()
        self.mantra_model = mantra_model

    def on_epoch_end(self, epoch, logs={}):

        if self.mantra_model.task:
            self.mantra_model.task.latest_loss = self.mantra_model.task.evaluate(self.mantra_model)

            print('%s: %s' % (self.mantra_model.task.evaluation_name, self.mantra_model.task.latest_loss))

            if hasattr(self.mantra_model.task, 'secondary_metrics'):

                self.mantra_model.task.secondary_metrics_values = {}

                for metric in self.mantra_model.task.secondary_metrics:
                    metric_result = getattr(self.mantra_model.task, metric)(self.mantra_model)
                    self.mantra_model.task.secondary_metrics_values[metric] = float(metric_result)
                    print('%s: %s' % (metric.capitalize(), metric_result))


class ModelCheckpoint(tf.keras.callbacks.Callback):
    """
    Stores the latest model weights at the end of epoch
    """
    def __init__(self, mantra_model):
        super(ModelCheckpoint, self).__init__()
        self.mantra_model = mantra_model

    def on_epoch_end(self, epoch, logs={}):

        checkpoint_dir = '%s/trials/%s/checkpoint/' % (os.getcwd(), self.mantra_model.trial.trial_folder_name)

        if not os.path.isdir(checkpoint_dir):
            os.makedirs(checkpoint_dir)

        if self.mantra_model.task:
            self.mantra_model.task.latest_loss = self.mantra_model.task.evaluate(self.mantra_model)

            if not hasattr(self.mantra_model.task, 'best_loss'):
                self.mantra_model.task.best_loss = None
                self.mantra_model.task.best_loss = self.mantra_model.task.latest_loss
                self.mantra_model.task.best_secondary_metrics_values = self.mantra_model.task.secondary_metrics_values.copy()

            if self.mantra_model.save_best_only:
                if self.mantra_model.task.latest_loss < self.mantra_model.task.best_loss:
                    self.mantra_model.model.save('%smodel_weights.h5' % checkpoint_dir)
                    self.mantra_model.task.best_loss = self.mantra_model.task.latest_loss
                    self.mantra_model.task.best_secondary_metrics_values = self.mantra_model.task.secondary_metrics_values.copy()
            else:
                self.mantra_model.model.save('%smodel_weights.h5' % checkpoint_dir)

        else:
            self.mantra_model.model.save('%smodel_weights.h5' % checkpoint_dir)


class StoreTrial(tf.keras.callbacks.Callback):
    """
    Store the trial data at the end of an epoch
    """

    def __init__(self, mantra_model):
        super(StoreTrial, self).__init__()
        self.mantra_model = mantra_model

    def on_epoch_end(self, epoch, logs={}):
        self.mantra_model.store_trial_data(epoch)


class TensorBoard:
    """
    Configures the Keras TensorBoard callback with the right directory in Mantra
    """
    def __new__(cls, mantra_model, **kwargs):

        log_dir = '%s/trials/%s/logs/' % (os.getcwd(), mantra_model.trial.trial_folder_name)

        return tf.keras.callbacks.TensorBoard(log_dir=log_dir, **kwargs)

