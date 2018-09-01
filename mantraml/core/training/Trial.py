import datetime
import os
from termcolor import colored
import yaml

from mantraml.core.hashing.MantraHashed import MantraHashed


SHORT_HASH_INT = 6 # taking a section of hash for folder names (e.g. 6 digits)
DEFAULT_EPOCHS = 200
DEFAULT_BATCH_SIZE = 64


class Trial:
    """
    Class holds methods for generating trial metadata and trial scripts
    """
    def __init__(self, project_name, model_name, dataset_name, task_name, cloud, args=None, **kwargs):
        """

        Parameters
        -----------

        project_name - str
            Name of the Mantra project

        model_name - str
            Name of the Mantra model folder

        dataset_name - str
            Name of the Mantra dataset folder

        task_name - str
            Name of the Mantra task folder

        cloud - bool
            Whether using cloud or not

        args : dict
            Optional arguments that were used for training
        """

        self.project_name = project_name
        self.model_name = model_name
        self.dataset_name = dataset_name
        self.task_name = task_name
        self.cloud = cloud
        self.args = args

        if args:
            self.arg_str, self.arg_dict = self.configure_arguments(args, **kwargs)

    @classmethod
    def parse_argument(cls, arg_str, arg_key, arg_value):
        """
        Parse Arguents in a a command parser string

        Parameters
        -----------

        arg_str - str
            The total argument string e.g. '--cloud --dev --epochs 20'

        arg_key - str
            An argument key from the argument dictionary, e.g. 'epochs' or 'batch_size'

        arg_value - str/int/bool
            The value of the argument, e.g. the value 20 for the key 'epochs'

        Returns
        -----------
        argument string, e.g. '--cloud', and the argument value, e.g True, 10, or 1.05
        """

        if arg_value is True:
            arg_str += ' --%s' % arg_key
        elif isinstance(arg_value, list):
            arg_str += ' --%s %s' % (arg_key, ' '.join(arg_value))
        elif arg_value not in [True, False]:
            if isinstance(arg_value, str):
                if '.' in arg_value and all([i.isnumeric() for i in arg_value.split('.',1)]):
                    arg_value = float(arg_value)
            
            arg_str += ' --%s %s' % (arg_key, arg_value)

        return arg_str, arg_value

    @classmethod
    def configure_arguments(cls, args, **kwargs):
        """
        Here we process the arguments and keyword arguments into a string that can be used for the command line
        execution from the cloud instances; we also store into a combined dictionary that we can use to record the
        hyperparameters for the trial

        Parameters
        -----------
        args : dict
            Optional arguments that were used for training

        Returns
        -----------
        str for command line, dictionary of all arguments entered

        E.g. '--cloud --dropout 0.5', {'cloud': True, 'dropout': 0.5}
        """

        arg_dict = {}
        arg_str = ''

        # First Process the Arguments

        for arg_key, arg_value in args.__dict__.items():

            converted_arg_value = arg_value

            if converted_arg_value and arg_key not in ['func', 'model_name', 'dataset', 'cloud']:
                arg_str, converted_arg_value = cls.parse_argument(arg_str, arg_key, converted_arg_value)                    
                arg_dict[arg_key] = converted_arg_value

        # Secondly any Keyword (additional) arguments

        for arg_key, arg_value in kwargs.items():
            converted_arg_value = arg_value
            arg_str, converted_arg_value = cls.parse_argument(arg_str, arg_key, converted_arg_value)   
            arg_dict[arg_key] = converted_arg_value

        return arg_str, arg_dict

    def configure_trial_metadata(self):
        """
        This method configures the trial metadata file. This file contains information on the training job, including the data, model and task used, 
        as well as things like hyperparameters, a training timestamp, and so on.

        Parameters
        -----------
        arg_dict : dict
            Containing arguments that were used for training
        """

        metadata = {}
        metadata['model_name'] = self.model_name
        metadata['data_name'] = self.dataset_name 
        metadata['model_hash'] = self.model_hash
        metadata['data_hash'] = self.data_hash

        if self.task_name is not None:
            metadata['task_name'] = self.task_name
            metadata['task_hash'] = self.task_hash
        else:
            metadata['task_name'] = 'none'
            metadata['task_hash'] = 'none'

        metadata['hyperparameters'] = self.get_hyperparameter_dict(metadata_dict=metadata)

        metadata['timestamp'] = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        metadata['trial_group_hash'] = MantraHashed.get_256_hash_from_string(metadata['model_hash'] + metadata['data_hash'] + metadata['task_hash'])
        metadata['trial_hash'] = MantraHashed.get_256_hash_from_string(metadata['model_hash'] + metadata['data_hash'] + metadata['task_hash'] + str(metadata['timestamp']))

        self.trial_folder_name = '%s_%s_%s_%s' % (metadata['timestamp'], metadata['model_name'], metadata['data_name'], metadata['trial_hash'][:SHORT_HASH_INT])
        self.yaml_content = yaml.dump(metadata, default_flow_style=False)
        self.log_file_contents = '%s %s %s %s %s %s %s %s %s %s\n' % (metadata['timestamp'], self.trial_folder_name, metadata['trial_hash'], 
            metadata['trial_group_hash'],
            metadata['model_name'],
            metadata['model_hash'],
            metadata['data_name'],
            metadata['data_hash'],
            metadata['task_name'],
            metadata['task_hash'])

    def get_hyperparameter_dict(self, metadata_dict):
        """
        This method extracts hyperparameters from the argument parser dictionary, and returns the dictionary. This method also 
        removes some parameters that are not treated as hyperparameters, and these are moved to top level keys in the metadata
        dictionary.

        Parameters
        -----------
        metadata_dict : dict
            A dictionary of metadata
        """

        hyperparm_dict = self.arg_dict.copy()

        for training_param in ['instance_ids', 'savebestonly', 'task', 'dev', 'cloudremote']:         
            if training_param in hyperparm_dict:
                metadata_dict[training_param] =  hyperparm_dict[training_param]
                hyperparm_dict.pop(training_param)

        if 'epochs' not in hyperparm_dict:
            hyperparm_dict['epochs'] = DEFAULT_EPOCHS

        if 'batch_size' not in hyperparm_dict:
            hyperparm_dict['batch_size'] = DEFAULT_BATCH_SIZE

        return hyperparm_dict

    def version_artefact(self, artefact_type='MODELS', **kwargs):
        """
        This method versions an artefacts used in the training: data, models tasks. We store to the .mantra folder - it means that we retrieve
        a hash for each artefact that we can record for the user in the UI; and also allows the user to retrieve old model
        or dataset versions on their local at any time.

        Parameters
        -----------
        artefact_type : str
            Specifies the type of DMT artefact (data-model-task)

        Returns
        -----------
        str - string to display to user containing the hashed artefact
        """

        if artefact_type == 'MODELS':
            folder_name = 'models'
            artefact_name = self.model_name
        elif artefact_type == 'DATA':
            folder_name = 'data'
            artefact_name = self.dataset_name 
        elif artefact_type == 'TASKS':
            folder_name = 'tasks'
            artefact_name = self.task_name 

        artefact_dir = '%s/%s/%s' % (os.getcwd(), folder_name, artefact_name)
        artefact_hash, artefact_hash_dict = MantraHashed.get_folder_hash(folder_dir=artefact_dir)
        
        is_new_artefact = MantraHashed.save_artefact(
            cwd=os.getcwd(), 
            hash=artefact_hash, 
            objects=artefact_hash_dict, 
            trial=self,
            artefact_type=artefact_type, **kwargs)
        
        if artefact_type == 'MODELS':
            self.model_hash = artefact_hash
            artefact_hash_text = colored(' \033[1m ...', 'white') + colored(' Model hash:        %s' % self.model_hash, 'blue')
        elif artefact_type == 'DATA':
            self.data_hash = artefact_hash
            artefact_hash_text = colored(' \033[1m ...', 'white') + colored(' Data hash:         %s' % self.data_hash, 'blue')
        elif artefact_type == 'TASKS':
            self.task_hash = artefact_hash
            artefact_hash_text = colored(' \033[1m ...', 'white') + colored(' Task hash:         %s' % self.task_hash, 'blue')

        if is_new_artefact:
            artefact_hash_text += colored(' (new)', 'white')

        return artefact_hash_text

    def version_artefacts(self, **kwargs):
        """
        This method versions the artefacts used in the training: data, models tasks. We store to the .mantra folder - it means that we retrieve
        a hash for each artefact that we can record for the user in the UI; and also allows the user to retrieve old model
        or dataset versions on their local at any time.

        Returns
        -----------
        void - versions the artefacts 
        """

        model_hash_text = self.version_artefact(artefact_type='MODELS', **kwargs)
        data_hash_text = self.version_artefact(artefact_type='DATA', **kwargs)
        if self.task_name is not None:
            task_hash_text = self.version_artefact(artefact_type='TASKS', **kwargs)

        print(colored(' \033[1m [+]', 'green') + colored(' Model, data and task artefacts versioned', 'white'))

        print(model_hash_text)
        print(data_hash_text)
        if self.task_name is not None:
            print(task_hash_text)

    def write_metadata_local(self, execute=True):
        """
        This method configures the trial metadata file. This file contains information on the training job, including the data, model and task used, 
        as well as things like hyperparameters, a training timestamp, and so on.

        Parameters
        -----------

        execute : bool
            If True, will write the file to a location; else will return a string (useful for testing)

        Returns
        -----------
        void - creates the metadata yaml and sends it to the instances; else returns the yaml file and log contents
        """

        if execute:
            os.system('echo "%s" > trial_metadata.yml' % self.yaml_content)

        if execute:
            f = open('%s/%s' % (os.getcwd(), '.mantra/TRIALS'), "a")
            f.write(self.log_file_contents)
            f.close()
        else:
            return self.yaml_content, self.log_file_contents
