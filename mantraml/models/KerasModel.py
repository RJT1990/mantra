import os, time, itertools, pickle
import lazy_import
tf = lazy_import.lazy_module("tensorflow")
np = lazy_import.lazy_module("numpy")
from .BaseModel import BaseModel


class KerasModel(BaseModel):
    """
    This model class defines a TensorFlow.keras model with integration for Mantra
    """

    def __init__(self, args=None, dataset=None, settings=None, trial=False, **kwargs):
        """
        Parameters
        -----------
        args - command line args
            Arguments from the Mantra command line 

        dataset - mantraml.Dataset type object 
            A mantraml.Dataset like object that contains the data and data processing

        settings - Python module
            Containing user settings (including cloud options)
        """

        super(KerasModel, self).__init__(args=args, dataset=dataset, settings=settings, trial=trial, **kwargs)

        self.optimizer = kwargs.get('optimizer', 'adam')
        self.loss = kwargs.get('loss', 'mean_squared_error')
        self.metrics = kwargs.get('metrics', ['accuracy'])
        self.loss_weights = kwargs.get('loss_weights', None)
        self.sample_weight_mode = kwargs.get('sample_weight_mode', None)
        self.weighted_metrics = kwargs.get('weighted_metrics', None)
        self.target_tensors = kwargs.get('target_tensors', None)

        self.model = self.build_model()

    def init_model(self):
        """
        This is a wrapper function for initiatilising the model, for example initialisation weights, or loading
        weights from a past checkpoint

        Returns
        -----------
        void - updates the model with initialisation variables
        """
        
        self.model.compile(
            loss=self.loss,
            optimizer=self.optimizer,
            metrics=self.metrics,
            loss_weights=self.loss_weights,
            sample_weight_mode=self.sample_weight_mode,
            weighted_metrics=self.weighted_metrics,
            target_tensors=self.target_tensors)

    def run(self):
        """
        Runs the training
        """
        
        # Build and initialize
        self.init_model()
        
        log_dir = '%s/trials/%s/logs/' % (os.getcwd(), self.trial_folder_name)
        checkpoint_dir = '%s/trials/%s/checkpoint/' % (os.getcwd(), self.trial_folder_name)

        if not os.path.isdir(checkpoint_dir):
            os.makedirs(checkpoint_dir)

        exp_callback = StoreTrials(mantra_model=self)
        eval_callback = EvaluateCallBack(mantra_model=self)
        tb_callback = tf.keras.callbacks.TensorBoard(log_dir=log_dir, histogram_freq=0, write_graph=True, write_images=True)
        checkpoint_callback = MantraModelCheckpoint(mantra_model=self)

        callbacks = [tb_callback, eval_callback, checkpoint_callback]
        callbacks.append(exp_callback)

        self.model.fit(self.X, self.y, epochs=self.n_epochs, batch_size=self.n_batch, 
            callbacks=callbacks)


class StoreTrials(tf.keras.callbacks.Callback):

    def __init__(self, mantra_model):
        super(StoreTrials, self).__init__()
        self.mantra_model = mantra_model

    def on_epoch_end(self, epoch, logs={}):
        self.mantra_model.store_trial_data(epoch)


class MantraModelCheckpoint(tf.keras.callbacks.Callback):

    def __init__(self, mantra_model):
        super(MantraModelCheckpoint, self).__init__()
        self.mantra_model = mantra_model

    def on_epoch_end(self, epoch, logs={}):

        checkpoint_dir = '%s/trials/%s/checkpoint/' % (os.getcwd(), self.mantra_model.trial_folder_name)

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


class EvaluateCallBack(tf.keras.callbacks.Callback):

    def __init__(self, mantra_model):
        super(EvaluateCallBack, self).__init__()
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