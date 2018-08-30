import os, time, itertools, pickle
import lazy_import
tf = lazy_import.lazy_module("tensorflow")
np = lazy_import.lazy_module("numpy")
from .BaseModel import BaseModel


class TFModel(BaseModel):
    """
    This model class defines a TensorFlow model with integration for mANTRA
    """

    def __init__(self, session=None, args=None, dataset=None, settings=None, trial=False, **kwargs):
        """
        Parameters
        -----------
        session - tf.Session() object
            A TensorFlow Session - can leave empty, in which case a default session is found or InteractiveSession is initialized
            
        args - command line args
            Arguments from the Mantra command line 

        dataset - mantraml.Dataset type object 
            A mantraml.Dataset like object that contains the data and data processing

        settings - Python module
            Containing user settings (including cloud options)

        trial - bool
            If True, will conduct a trial and configure storage for it
        """

        super(TFModel, self).__init__(args=args, dataset=dataset, settings=settings, trial=trial, **kwargs)

        # Configure GPU
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = kwargs.get('allow_growth', True)
        config.gpu_options.per_process_gpu_memory_fraction = kwargs.get('per_process_gpu_memory_fraction', 0.90)
        
        if session:
            self.session = session
        elif tf.get_default_session() is None:
            self.session = tf.InteractiveSession(config=config)
        else:
            self.session = tf.get_default_session()

    def save_model_weights(self):
        """
        At the end of each epoch we save the model weights as a checkpoint. This functionality should occur here.

        Returns
        ----------
        void - updates parameters
        """
        
        if self.task:
            self.task.latest_loss = self.task.evaluate(self)

            if not hasattr(self.task, 'best_loss'):
                self.task.best_loss = None
                self.task.best_loss = self.task.latest_loss

            if self.save_best_only:
                if self.task.latest_loss < self.task.best_loss:
                    self.saver.save(self.session, '%s/trials/%s/checkpoint/' % (os.getcwd(), self.trial_folder_name))
                    self.task.best_loss = self.task.latest_loss
            else:
                self.saver.save(self.session, '%s/trials/%s/checkpoint/' % (os.getcwd(), self.trial_folder_name))

        else:
            self.saver.save(self.session, '%s/trials/%s/checkpoint/' % (os.getcwd(), self.trial_folder_name))

    def init_model(self):
        """
        This is a wrapper function for initiatilising the model, for example initialisation weights, or loading
        weights from a past checkpoint

        Returns
        -----------
        void - updates the model with initialisation variables
        """
        
        self.saver = tf.train.Saver()  

        tf.global_variables_initializer().run()

        self.writer = tf.summary.FileWriter('%s/trials/%s/logs/' % (os.getcwd(), self.trial_folder_name))
        self.summary = tf.summary.merge_all()
        self.writer.add_graph(self.session.graph)

