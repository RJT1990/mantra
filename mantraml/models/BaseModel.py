import os, time, itertools, pickle
from termcolor import colored

import lazy_import
np = lazy_import.lazy_module("numpy")
yaml = lazy_import.lazy_module("yaml")
shutil = lazy_import.lazy_module("shutil")

import datetime

from mantraml.core.cloud import AWS

from .consts import METADATA_FILE_NAME, SHORT_HASH_INT, DEFAULT_EPOCHS, DEFAULT_BATCH_SIZE


class BaseModel:
    """
    This model class defines a Base model with integration for Mantra
    """

    def __init__(self, args=None, settings=None, dataset=None, trial=False, **kwargs):
        """
        Parameters
        -----------

        args - command line args
            Arguments from the Mantra command line 

        settings - Python module
            Containing user settings (including cloud options)

        dataset - mantraml.Dataset type object 
            A mantraml.Dataset like object that contains the data and data processing

        trial - bool
            If True, will conduct a trial and configure storage for it
        """

        if not dataset:
            err_msg = '''BaseModel did not receive a dataset argument.

            A common reason for this is that your model class does not inherit properly from
            the parent classes. Your model's __init__ function should have a line near the top
            that looks like:

            super().__init__(session=session, dataset=dataset, **kwargs) # TensorFlow model inheritance

            This way the dataset gets passed to the BaseModel methods and can be processed properly.
            '''

            raise ValueError(err_msg)

        else:
            self.data = dataset

        self.args = args # command line arguments
        self.settings = settings
        self.trial = trial

        # Set any user commands
        if self.args.batch_size:
            self.n_batch = self.args.batch_size
        else:
            self.n_batch = DEFAULT_BATCH_SIZE

        if self.args.epochs:
            self.n_epochs = self.args.epochs
        else:
            self.n_epochs = DEFAULT_EPOCHS

        if self.args.savebestonly:
            self.save_best_only = True
        else:
            self.save_best_only = False

        if self.trial:
            self.configure_trial_metadata()

        self._X = None
        self._y = None
        self._X_test = None
        self._y_test = None

    @property
    def X(self):
        """
        Retrives the feature data from either the self.task object, or 
        if the task doesn't exist, the self.data object.

        Returns
        --------
        np.ndarray of feature data        
        """

        if self._X is not None:
            return self._X

        if hasattr(self, 'task'):
            if self.task is not None:
                self._X, self._y = self.task.get_training_data()
                return self._X

        self._X = self.data.X

        return self._X

    @property
    def y(self):
        """
        Retrives the labels data from either the self.task object, or 
        if the task doesn't exist, the self.data object.

        Returns
        --------
        np.ndarray of label data        
        """

        if self._y is not None:
            return self._y

        if hasattr(self, 'task'):
            if self.task is not None:
                self._X, self._y = self.task.get_training_data()
                return self._y

        self._y = self.data.y

        return self._y

    @property
    def X_test(self):
        """
        Retrives the feature data from either the self.task object, or 
        if the task doesn't exist, the self.data object.

        Returns
        --------
        np.ndarray of feature data        
        """

        if self._X_test is not None:
            return self._X_test

        if hasattr(self, 'task'):
            if self.task is not None:
                self._X_test, self._y_test = self.task.get_test_data()
                return self._X_test

        self._X_test = self.data.X

        return self._X_test

    @property
    def y_test(self):
        """
        Retrives the labels data from either the self.task object, or 
        if the task doesn't exist, the self.data object.

        Returns
        --------
        np.ndarray of label data        
        """

        if self._y_test is not None:
            return self._y_test

        if hasattr(self, 'task'):
            if self.task is not None:
                self._X_test, self._y_test = self.task.get_test_data()
                return self._y_test

        self._y_test = self.data.y

        return self._y_test

    def configure_trial_metadata(self):
        """
        Configure the metadata for a new trial 

        Returns
        -----------
        void - updates the instance with model variables
        """

        metadata_location = '%s/%s' % (os.getcwd(), METADATA_FILE_NAME)
        metadata = yaml.load(open(metadata_location, 'r'))
        self.trial_folder_name = '%s_%s_%s_%s' % (metadata['timestamp'], metadata['model_name'], metadata['data_name'], metadata['trial_hash'][:SHORT_HASH_INT])
        trial_location = os.getcwd() + '/trials/%s' % self.trial_folder_name

        if not os.path.isdir('%s/%s' % (os.getcwd(), 'trials')):
            os.mkdir('%s/%s' % (os.getcwd(), 'trials'))

        os.mkdir(trial_location)
        shutil.move(metadata_location, '%s/%s' % (trial_location, METADATA_FILE_NAME))

    def build_model(self):
        """
        This is a wrapper function for building the model. This function contains architecture and other objects
        that are used to create the computational graph (and/or model).

        Returns
        -----------
        void - updates the instance with model variables
        """

        return

    def end_of_epoch_update(self, epoch):
        """
        Update to apply at the end of the epoch
        """

        return
          
    def end_of_training_update(self):
        """
        Update to apply at the end of training
        """

        return

    def format_data(self):
        """
        This is a wrapper function for obtaining the training data

        Returns
        -----------
        list - containing the training data
        """

        return []

    def define_logs(self):
        """
        Define terms to log here

        Returns
        ----------
        void - updates parameters
        """

        return

    def save_model_weights(self):
        """
        At the end of each epoch we save the model weights as a checkpoint. This functionality should occur here.

        Returns
        ----------
        void - updates parameters
        """

        return

    def gradient_update(self, iter):
        """
        Updates the parameters with a single gradient update

        Parameters
        ----------
        iter - int
            The iteration number

        Returns
        ----------
        void - updates parameters
        """

        return

    def store_trial_data(self, epoch):
        """
        This function stores trial data - e.g. S3
        """
        
        # update trial metadata
        trial_location = os.getcwd() + '/trials/%s' % self.trial_folder_name
        metadata_location = '%s/%s' % (trial_location, METADATA_FILE_NAME)
        
        with open(metadata_location, 'r') as stream:
            yaml_content = yaml.load(stream)

        if epoch + 1 == self.n_epochs:
            yaml_content['training_finished'] = True
        else:
            yaml_content['training_finished'] = False

        yaml_content['current_epoch'] = epoch + 1

        if self.task:
            if self.save_best_only:
                yaml_content['validation_loss'] = float(self.task.best_loss)

                if hasattr(self.task, 'secondary_metrics'):
                    yaml_content['secondary_metrics'] = self.task.best_secondary_metrics_values

            else:
                yaml_content['validation_loss'] = float(self.task.latest_loss)
        
                if hasattr(self.task, 'secondary_metrics'):
                    yaml_content['secondary_metrics'] = self.task.secondary_metrics_values

        new_yaml_content = yaml.dump(yaml_content, default_flow_style=False)

        yaml_file = open(metadata_location, 'w')
        yaml_file.write(new_yaml_content)
        yaml_file.close()

        # send to S3
        AWS.export_trials_to_s3(model=self)

    def run(self):
        """
        Runs the training.
        """
        
        # Build and initialize
        self.build_model()

        if self.trial:
            self.define_logs()
                
        self.init_model()

        # Ready data
        self.batches_per_epoch = len(self.data) // self.n_batch
            
        # Results Dict
        np.random.seed(int(time.time())) # random seed for training
        
        for epoch in range(self.n_epochs):
            self.epoch_start_time = time.time()

            for iter in range(self.batches_per_epoch):
                self.gradient_update(iter)

            self.end_of_epoch_update(epoch)

            if self.trial:
                self.save_model_weights()
                self.store_trial_data(epoch)

            print(colored('🤖 ', 'blue') + colored(' \033[1m Epoch [%d/%d] Complete' % ((epoch+1), self.n_epochs), 'green') + ' %.2f seconds' % (time.time() - self.epoch_start_time))

        self.end_of_training_update()