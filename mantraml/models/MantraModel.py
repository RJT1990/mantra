import datetime
import os
from termcolor import colored

import lazy_import
np = lazy_import.lazy_module("numpy")
yaml = lazy_import.lazy_module("yaml")
shutil = lazy_import.lazy_module("shutil")

from mantraml.core.cloud.AWS import AWS

from .consts import METADATA_FILE_NAME, SHORT_HASH_INT, DEFAULT_EPOCHS, DEFAULT_BATCH_SIZE


class MantraModel:
    """
    By inheriting from this MantraModel class, a deep learning model gets access to Mantra integration, including cloud integration, model monitoring
    and more. The core methods below link the model with configuration and training metadata.
    """

    # default training arguments
    batch_size = 64
    epochs = 200

    def configure_core_arguments(self, args):
        """
        This method adds core training attributes from an argument parser namespace (args) such as the number of epochs, the batch size, and more

        Parameters
        -----------
        args - Argument parser namespace
            Containing training arguments such as batch size, number of epochs

        Returns
        -----------
        void - update self with new attributes
        """

        if args.batch_size is not None:
            self.batch_size = args.batch_size
        else:
            self.batch_size = DEFAULT_BATCH_SIZE

        if args.epochs is not None:
            self.epochs = args.epochs
        else:
            self.epochs = DEFAULT_EPOCHS

        if args.savebestonly is not None:
            self.save_best_only = True
        else:
            self.save_best_only = False

    def end_of_epoch_message(self, epoch, message):
        """
        A cute method for printing a message at the end of an epoch

        Parameters
        -----------
        epoch - int
            The epoch number

        message - str
            A message to print at the end of the epoch

        Returns
        -----------
        void - prints a message
        """

        print(colored('🤖 ', 'blue') + colored(' \033[1m Epoch [%d/%d] Complete' % ((epoch+1), self.epochs), 'green') + ' %s' % message)

    def sync_trial_metadata(self):
        """
        Sync the metadata for a new trial 

        Returns
        -----------
        void - updates the instance with model variables
        """

        metadata_location = '%s/%s' % (os.getcwd(), METADATA_FILE_NAME)
        metadata = yaml.load(open(metadata_location, 'r'))

        self.trial.trial_folder_name = '%s_%s_%s_%s' % (metadata['start_timestamp'], metadata['model_name'], metadata['data_name'], metadata['trial_hash'][:SHORT_HASH_INT])
        trial_location = os.getcwd() + '/trials/%s' % self.trial.trial_folder_name

        if not os.path.isdir('%s/%s' % (os.getcwd(), 'trials')):
            os.mkdir('%s/%s' % (os.getcwd(), 'trials'))

        os.mkdir(trial_location)
        shutil.move(metadata_location, '%s/%s' % (trial_location, METADATA_FILE_NAME))

    def store_trial_data(self, epoch):
        """
        Stores trial data in the trial metadata file, and then, if cloud training, sends the trial data to S3 for storage

        Parameters
        -----------
        epoch - int
            The epoch number (zero indexed)

        Returns
        -----------
        void - updates a training yml file and sends trial data to S3
        """
        
        # update trial metadata
        trial_location = os.getcwd() + '/trials/%s' % self.trial.trial_folder_name
        metadata_location = '%s/%s' % (trial_location, METADATA_FILE_NAME)
        
        with open(metadata_location, 'r') as stream:
            yaml_content = yaml.load(stream)

        new_yaml_content = self.update_trial_metadata(yaml_content, epoch)

        yaml_file = open(metadata_location, 'w')
        yaml_file.write(new_yaml_content)
        yaml_file.close()

        if hasattr(self, 'cloudremote'):
            if self.cloudremote:
                AWS.export_trials_to_s3(model=self)

    def update_trial_metadata(self, yaml_content, epoch):
        """
        Updates the trial metadata yaml file with the latest trial information

        Parameters
        -----------
        yaml_content - dict
            Dictionary containing the existing yaml content

        epoch - int
            The epoch number (zero indexed)

        Returns
        -----------
        void - updates a training yml file and sends trial data to S3
        """

        if epoch + 1 == self.epochs:
            yaml_content['training_finished'] = True
            yaml_content['end_timestamp'] = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        else:
            yaml_content['training_finished'] = False

        yaml_content['current_epoch'] = epoch + 1

        if 'validation_loss_history' not in yaml_content:
            yaml_content['validation_loss_history'] = []

        if self.task:
            if self.save_best_only:
                yaml_content['validation_loss'] = float(self.task.best_loss)

                if hasattr(self.task, 'secondary_metrics'):
                    yaml_content['secondary_metrics'] = self.task.best_secondary_metrics_values

            else:
                yaml_content['validation_loss'] = float(self.task.latest_loss)
        
                if hasattr(self.task, 'secondary_metrics'):
                    yaml_content['secondary_metrics'] = self.task.secondary_metrics_values

            yaml_content['validation_loss_history'].append(float(self.task.latest_loss))

        return yaml.dump(yaml_content, default_flow_style=False)


