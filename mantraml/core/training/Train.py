import importlib
import os
import sys
from termcolor import colored

from mantraml.core.cloud.AWS import AWS
from mantraml.core.training.Trial import Trial
from mantraml.data.finders import find_dataset_class, find_model_class, find_task_class, find_framework

from .consts import CONFIG_VARIABLES


class Train:
    """
    This class contains methods 
    """

    def __init__(self, project_name, settings, args, **kwargs):
        """
        Parameters
        -----------

        project_name - str
            The name of the Mantra project

        settings - module
            An Mantra settings module

        args - Namespace from an ArgumentParser
            Arguments from the command line

        kwargs - keyword arguments
            Additional unknown arguments
        """

        self.project_name = project_name
        self.settings = settings
        self.args = args
        self.kwargs = kwargs

        self.dataset_name = args.dataset
        self.model_name = args.model_name
        self.task_name = args.task
        self.cloudremote = args.cloudremote
        self.instance_ids = args.instance_ids
        self.cloud = args.cloud
        self.dev = args.dev

    def begin(self):
        """
        Wrapper interface command to begin training - either locally or cloud
        """

        if self.cloud:
            self.begin_cloud()
        else:
            self.begin_local()

    def begin_cloud(self):
        """
        This command trains on a cloud provider. We find the cloud settings in the settings file, and then we initialise a cloud based class. We then
        call setup - which sets up the cloud instances for training - and then we begin with train().
        """

        if any([not hasattr(self.settings, config_var) for config_var in CONFIG_VARIABLES]):
            raise AttributeError(colored('You have not set up your cloud configuration yet. To do this run:\n', 'red') + colored(' mantra cloud', 'blue'))

        # Obtain Dataset

        sys.path.append(os.getcwd())
        data_module = importlib.import_module("data.%s.data" % self.dataset_name)
        dataset_class = find_dataset_class(data_module)

        # Find Model Framework
        model_module = importlib.import_module("models.%s.model" % self.model_name)
        model_framework = find_framework(model_module)

        # Cloud Configuration

        if self.settings.CLOUD_PROVIDER == 'AWS':
            CloudClass = AWS
        else:
            return

        cloud_instance = CloudClass(settings=self.settings, instance_ids=self.instance_ids, project_name=self.project_name, 
            dataset_class=dataset_class, dev=self.dev, framework=model_framework)
        cloud_instance.setup(args=self.args, **self.kwargs)
        cloud_instance.train(args=self.args)

    def begin_local(self):
        """
        This command trains locally. This command is either called through direct local training on the user's machine when --cloud isn't specified, or alternatively, 
        it is called on the cloud machine itself, in which case we have a --cloudremote flag so we know that we are reporting data through SSH back to the local machine.
        """

        # Obtain Dataset

        sys.path.append(os.getcwd())
        data_module = importlib.import_module("data.%s.data" % self.dataset_name)
        dataset_class = find_dataset_class(data_module)

        if not dataset_class:
            return

        dataset = dataset_class(name=self.dataset_name, trial=True, **self.kwargs)
        dataset.configure_core_arguments(self.args)
        
        # Obtain the model class

        model_module = importlib.import_module("models.%s.model" % self.model_name)
        model_class = find_model_class(model_module)

        # Obtain the task class
            
        task_class = None

        if self.task_name is not None:
            task_module = importlib.import_module("tasks.%s.task" % self.task_name)
            task_class = find_task_class(task_module)

        if task_class is None:
            task = None
        else:
            task = task_class(data=dataset)

        if not model_class:
            return

        model = model_class(data=dataset, task=task, **self.kwargs)
        model.args = self.args
        model.settings = self.settings
        model.cloudremote = self.cloudremote
        model.configure_core_arguments(self.args)

        if not self.cloudremote: # local training
            self.setup_local_training(model)
        else:
            model.trial = Trial(project_name=self.project_name, 
            model_name=self.model_name, 
            dataset_name=self.dataset_name, 
            task_name=self.task_name, 
            cloud=self.cloud)

        model.sync_trial_metadata()

        if not self.cloudremote: 
            print(colored('\n \033[1m Training\n', 'blue'))

        model.run()

    def setup_local_training(self, model):
        """
        This method setups the MantraModel instance with trial support, so that we can record during local training

        Parameters
        -----------
        model - MantraModel object
            The model that is going to be trained
        """

        print(colored('\n \033[1m Mantra Training', 'blue') + colored('\033[1m 🚀\n', 'green'))

        print(colored('\n \033[1m Setup\n', 'blue'))

        # Trial Operations
        model.trial = Trial(project_name=self.project_name, 
            model_name=self.model_name, 
            dataset_name=self.dataset_name, 
            task_name=self.task_name, 
            cloud=self.cloud, 
            args=self.args, **self.kwargs)
        model.trial.version_artefacts()
        model.trial.configure_trial_metadata()
        model.trial.write_metadata_local()