import datetime
import lazy_import
import os
import subprocess
import sys
import time
from termcolor import colored
import threading
import yaml

boto3 = lazy_import.lazy_module("boto3")
paramiko = lazy_import.lazy_module("paramiko")

import logging
logging.getLogger('boto3').setLevel(logging.CRITICAL)
logging.getLogger('botocore').setLevel(logging.CRITICAL)
logging.getLogger('paramiko').setLevel(logging.CRITICAL)

from mantraml.core.hashing.MantraHashed import MantraHashed
from mantraml.models.consts import SHORT_HASH_INT, DEFAULT_BATCH_SIZE, DEFAULT_EPOCHS

from .consts import DEFAULT_SH_SCRIPT, DEFAULT_SH_SCRIPT_VERBOSE, DEFAULT_SH_TASK_SCRIPT, DEFAULT_SH_TASK_SCRIPT_VERBOSE
from .consts import EXCLUDED_PROJECT_FILES, MANTRA_DEVELOPMENT_TAG_NAME


class AWS:
    """
    This class contains methods for interacting with AWS : with a focus on the following functionality:

        - Launching new reserved GPU instances on the user's request for training, and configuring dependencies
        - Moving Mantra projects to the cloud for training
        - Retrieving the results of training in the cloud and returning them to a local server
    """

    def __init__(self, settings=None, instance_ids=None, dataset_class=None, dev=False, project_name='default'):
        """
        Parameters
        -----------

        settings : Python module
            List of Mantra consts that determines AWS parameters such as region, instance type, and so on

        instance_ids : list
            If not None, will use provided instances for training; else will create new instances (unless dev is specified)

        dataset_class : Dataset class
            The Dataset to be sent to S3, which is contained in your data folder, e.g. "Cifar10" class <> "/data/cifar_10"

        dev : bool
            If true, loads up (or creates) a development machine that does not terminate after job completion. Otherwise will
            create new instances.

        project_name : str
            The name of the Mantra projects - this string is used for folder creation on the cloud instances; arbitrary.

        """

        print(colored('\n \033[1m Mantra Training', 'blue') + colored('\033[1m 🚀\n', 'green'))

        print(colored(' \033[1m Setup\n', 'blue'))

        self.settings = settings
        self.instance_ids = instance_ids
        self.dataset_class = dataset_class
        self.dev = dev
        self.project_name = project_name

        self.ec2 = boto3.resource('ec2')

        self.get_training_instances()
        self.run_training_instance()
        self.create_ssh_client()

        print(colored(' \033[1m [+]', 'green') + colored(' Cloud connection established : using %s GPU instances' % str(1), 'white'))

    @classmethod
    def export_trials_to_s3(cls, model, execute=True):
        """
        This method exports trial data to the user's S3.

        Parameters
        -----------
        model : atlasml.Model object
            Model from which we'll get the information about the trial folder

        execute : bool
            If True, will execute the command; else will return the command as a string

        Returns
        -----------
        void - sends files from S3 to local, or str if no execution
        """

        path = '%s/trials/%s/' % (os.getcwd(), model.trial_folder_name)

        # s3 bucket locations
        s3_model_bucket_dir = 'trials/%s/' % model.trial_folder_name

        aws_cmd = 'aws s3 --exact-timestamps sync --quiet %s s3://%s/%s' % (path, model.settings.S3_BUCKET_NAME, s3_model_bucket_dir)
        
        if execute:
            os.system(aws_cmd)
        else:
            return aws_cmd

    @classmethod
    def sync_data(cls, args, settings, execute=True):
        """
        This method retrieves data from S3 and sends to the user's local machine

        Parameters
        -----------
        args : dict
            Arguments that were used in an Mantra command

        settings : Python module
            List of Mantra consts that determines AWS parameters

        execute : bool
            If True, will execute the command; else will return the command as a string

        Returns
        -----------
        void - sends files from S3 to local, or str if no execution
        """

        if args.artefact == 'trials':
            aws_cmd = 'aws s3 --exact-timestamps sync s3://%s/trials trials' % (settings.S3_BUCKET_NAME)
        elif args.artefact == 'data':
            if execute:
                if input("This will overwrite same-name files in your data directory. Are you sure? (y/n)\n") != "y":
                    exit()
            aws_cmd = 'aws s3 --exact-timestamps sync s3://%s/data data' % (settings.S3_BUCKET_NAME)
        else:
            aws_cmd = None

        if execute:
            os.system(aws_cmd)
        else:
            return aws_cmd

        print(colored('\n \033[1m [+]', 'green') + colored(' Sync complete\n', 'white'))

    @staticmethod
    def configure_arguments(args, **kwargs):
        """
        Here we process the arguments and keyword arguments into a string that can be used for the command line
        execution from the AWS instances; we also store into a combined dictionary that we can use to record the
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

            if arg_value and arg_key not in ['func', 'model_name', 'dataset', 'cloud']:
                if arg_value is True:
                    arg_str += ' --%s' % arg_key
                elif isinstance(arg_value, list):
                    arg_str += ' --%s %s' % (arg_key, ' '.join(arg_value))
                elif arg_value not in [True, False]:
                    if isinstance(arg_value, str):
                        if '.' in arg_value and all([i.isnumeric() for i in arg_value.split('.',1)]):
                            converted_arg_value = float(arg_value)
                    
                    arg_str += ' --%s %s' % (arg_key, arg_value)
                    
                arg_dict[arg_key] = converted_arg_value

        # Secondly any Keyword (additional) arguments

        for arg_key, arg_value in kwargs.items():

            converted_arg_value = arg_value 
            
            if arg_value is True:
                arg_str += ' --%s' % arg_key
            elif isinstance(arg_value, list):
                arg_str += ' --%s %s' % (arg_key, ' '.join(arg_value))
            elif arg_value not in [True, False]:
                if isinstance(arg_value, str):
                    if '.' in arg_value and all([i.isnumeric() for i in arg_value.split('.',1)]):
                        converted_arg_value = float(arg_value)

                arg_str += ' --%s %s' % (arg_key, converted_arg_value)
            
            arg_dict[arg_key] = converted_arg_value

        return arg_str, arg_dict

    def configure_trial_metadata(self, args, arg_dict, execute=True):
        """
        This method configures the trial metadata file. This file contains information on the training job, including the data, model and task used, 
        as well as things like hyperparameters, a training timestamp, and so on.

        Parameters
        -----------
        args : Namespace
            Optional arguments that were used for training

        arg_dict : dict
            Containing arguments that were used for training

        execute : bool
            If True, will write the file to a location; else will return a string (useful for testing)

        Returns
        -----------
        void - creates the metadata yaml and sends it to the instances; else returns the yaml file and log contents
        """

        metadata = {}
        metadata['model_name'] = args.model_name
        metadata['data_name'] = args.dataset 
        metadata['model_hash'] = self.model_hash
        metadata['data_hash'] = self.data_hash

        if args.task:
            metadata['task_name'] = args.task
            metadata['task_hash'] = self.task_hash
        else:
            metadata['task_name'] = 'none'
            metadata['task_hash'] = 'none'

        metadata['hyperparameters'] = arg_dict.copy()

        for training_param in ['instance_ids', 'savebestonly', 'task', 'dev']:         
            if training_param in metadata['hyperparameters']:
                metadata[training_param] =  metadata['hyperparameters'][training_param]
                metadata['hyperparameters'].pop(training_param)

        if 'epochs' not in arg_dict:
            metadata['hyperparameters']['epochs'] = DEFAULT_EPOCHS

        if 'batch_size' not in arg_dict:
            metadata['hyperparameters']['batch_size'] = DEFAULT_BATCH_SIZE

        metadata['timestamp'] = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        metadata['trial_group_hash'] = MantraHashed.get_256_hash_from_string(metadata['model_hash'] + metadata['data_hash'] + metadata['task_hash'])
        metadata['trial_hash'] = MantraHashed.get_256_hash_from_string(metadata['model_hash'] + metadata['data_hash'] + metadata['task_hash'] + str(metadata['timestamp']))

        yaml_content = yaml.dump(metadata, default_flow_style=False)

        if execute:
            self.client.exec_command('cd %s; echo "%s" > trial_metadata.yml' % (self.project_name, yaml_content))

        # Write data to TRIALS file for record keeping

        self.trial_folder_name = '%s_%s_%s_%s' % (metadata['timestamp'], metadata['model_name'], metadata['data_name'], metadata['trial_hash'][:SHORT_HASH_INT])
        
        file_contents = '%s %s %s %s %s %s %s %s %s %s\n' % (metadata['timestamp'], self.trial_folder_name, metadata['trial_hash'], 
            metadata['trial_group_hash'],
            metadata['model_name'],
            metadata['model_hash'],
            metadata['data_name'],
            metadata['data_hash'],
            metadata['task_name'],
            metadata['task_hash'])

        if execute:
            f = open('%s/%s' % (os.getcwd(), '.mantra/TRIALS'), "a")
            f.write(file_contents)
            f.close()
        else:
            return yaml_content, file_contents

    def create_instance(self):
        """
        This method creates a new EC2 instance. The instance image, security group and other settings will be determined by
        the settings in your project settings.py file. This method simply reads the configuration details from this file.

        The output is an EC2 instances object stored in self.instances.
        """

        additional_args = {}

        if self.settings.AWS_SECURITY_GROUP:
            additional_args['SecurityGroupIds'] = [self.settings.AWS_SECURITY_GROUP]

        print(colored(' \033[1m [-]', 'white') + colored(' Creating a %s instance' % self.settings.AWS_INSTANCE_TYPE, 'white'))

        instance_ids = self.ec2.create_instances(
            ImageId=self.settings.AWS_AMI_IMAGE_ID, 
            KeyName=self.settings.AWS_KEY_PATH.split('/')[-1].replace('.pem', ''), 
            MinCount=1, 
            MaxCount=1, 
            InstanceType=self.settings.AWS_INSTANCE_TYPE,
            **additional_args)
        self.instances = self.ec2.instances.filter(InstanceIds=[instance_ids[0].id])

        instance = [instance for instance in self.instances][0]
        instance.wait_until_running()

        if self.dev:
            self.ec2.create_tags(Resources=[instance.id], Tags=[{'Key':'Name', 'Value': MANTRA_DEVELOPMENT_TAG_NAME}])

        print(colored(' \033[1m [+]', 'green') + colored(' Instance now running', 'white'))

    def create_s3_bucket(self, s3_client, s3_buckets):
        """"
        This method creates an S3 Mantra project bucket if the user has not already created it. The name of the bucket
        is determined by the project settings.py file, specifically the S3_BUCKET_NAME const. 

        Parameters
        -----------
        s3_client - boto3 client
            The client to perform the operations with

        s3_buckets - list
            List of strs representing S3 bucket names in the user's S3
        """

        if self.settings.S3_BUCKET_NAME not in s3_buckets:
            kwargs = {}
            if self.settings.S3_AVAILABILITY_ZONE != 'us-east-1':
                kwargs = {'CreateBucketConfiguration': {'LocationConstraint': self.settings.S3_AVAILABILITY_ZONE}}
            s3_client.create_bucket(ACL='private', Bucket=self.settings.S3_BUCKET_NAME, **kwargs)

    def create_ssh_client(self):
        """
        This method creates the SSH client that we use to connect to the instance, so we can set it up for training, and
        report back training logs and console output.

        It stores the paramiko.SSHClient instance at self.client.
        """

        self.key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(self.settings.AWS_KEY_PATH))
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.public_dns, username="ubuntu", pkey=self.key)

    def export_data_to_s3(self, args):
        """
        This method exports data module dependencies to the user's S3. 

        - We check for the existence of an Mantra bucket. If it doesn't exist we create one. 
        - Next we check the files class variable in the dataset class....
        - We calculate the (concatenated) hash of the files; if it differs from what we have on S3, we reupload.
        - In other words, we are only storing the data dependencies on S3 for convenience: the rest we treat as small code files that 
            we can transfer easily between local/instances/S3 (e.g. data processing code)
    
        Parameters
        -----------

        args : list
            Optional arguments that were used for training

        Returns
        -----------
        void - setups the instance with the appropriate environment and files
        """

        data_dir = '%s/data/%s/' % (os.getcwd(), args.dataset)
        config_dir = '%sconfig.yml' % data_dir
        s3_data_bucket_dir = 'data/%s/raw/' % args.dataset
        s3_data_hash_location = '%shash' % s3_data_bucket_dir

        # Hashing details
        local_data_dependency_hash = MantraHashed.get_data_dependency_hash(data_dir=data_dir, dataset_class=self.dataset_class)

        s3_client = boto3.client('s3')
        s3_resource = boto3.resource('s3')
        s3_buckets = [bucket['Name'] for bucket in s3_client.list_buckets()['Buckets']]

        self.create_s3_bucket(s3_client, s3_buckets)

        try:
            bucket_contents = [object['Key'] for object in s3_client.list_objects(Bucket=self.settings.S3_BUCKET_NAME)['Contents']]
        except KeyError:
            bucket_contents = []

        hash_object = s3_resource.Object(self.settings.S3_BUCKET_NAME, s3_data_hash_location)

        if s3_data_hash_location in bucket_contents:

            s3_hash = hash_object.get()['Body'].read().decode('utf-8')

            if s3_hash == local_data_dependency_hash:
                print(colored(' \033[1m [+]', 'green') + colored(' Data exported to S3', 'white'))
                return

        # If the hash is different, or we don't have the files in S3, then upload the dataset dependencies to S3
        for file in self.dataset_class.files:
            s3_client.upload_file('%sraw/%s' % (data_dir, file), self.settings.S3_BUCKET_NAME, '%s%s' % (s3_data_bucket_dir, file), 
                Callback=S3ProgressPercentage('%sraw/%s' % (data_dir, file)))

        hash_object.put(Body=local_data_dependency_hash)

        print(colored('\n \033[1m [+]', 'green') + colored(' Data exported to S3', 'white'))

    def export_project_files_to_instances(self, execute=True):
        """
        This method exports the Mantra project files from your local directory straight to the instances. 

        We exclude a view folder/file types from transfer:
        - raw folder - the raw data folder (dependencies) is instead transferred from S3 to the instances 
        - trials folder - we don't need old trial data for running new trials
        - .extract folder - any data extracted for local training should not be sent over
        - .mantra folder - we don't need all the versioning data for training

        Parameters
        -----------
        execute : bool
            If True, will execute the command; else will return the command as a string

        Returns
        -----------
        void - sends files from S3 to local, or str if no execution
        """

        exclude_string = ' '.join(["--exclude %s" % ex_folder for ex_folder in EXCLUDED_PROJECT_FILES])
        rsync_string = "rsync -avL %s --progress -e 'ssh -i %s' %s ubuntu@%s:/home/ubuntu/%s > /dev/null" % (exclude_string, 
            self.settings.AWS_KEY_PATH, './', self.public_dns, self.project_name)
        
        if execute:
            os.system(rsync_string)
            print(colored(' \033[1m [+]', 'green') + colored(' Project files moved to instances', 'white'))
        else:
            return rsync_string

    def get_training_data_from_s3(self, output, send_weights=False, force=False, execute=True):
        """
        This method retrieves training data from S3 and sends to the user's local machine

        Parameters
        -----------

        output - str
            The latest stdout line from training

        send_weights - bool
            If true, send the model weights from S3 to local

        force : bool
            If force, force the sync (irrespective of content in the stdout)

        execute : bool
            If True will execute, else returns string

        Returns
        -----------
        void - sends files from S3 to local; or returns string if execute is off
        """
        
        if ('Epoch' in output) or force: # each time we have a new epoch of training, we send the files to local
            if send_weights:    
                aws_cmd = 'aws s3 --quiet --exact-timestamps sync s3://%s/trials/%s trials/%s' % (self.settings.S3_BUCKET_NAME, self.trial_folder_name, self.trial_folder_name)
            else:
                aws_cmd = "aws s3 --quiet --exact-timestamps sync s3://%s/trials/%s trials/%s --exclude 'checkpoint/*'" % (self.settings.S3_BUCKET_NAME, self.trial_folder_name, self.trial_folder_name)

            if execute:
                os.system(aws_cmd)
            else:
                return aws_cmd

    def get_training_instances(self):
        """
        This method creates or retrieves the instances to be used for training. The three options are:
        
        - Using existing instances - through self.instance_ids
        - Using a development instance - through self.dev (if a development instance doesn't exist, it will be created)
        - Creating new, temporary instances - else will set up new instances and terminate them once training is complete
        """

        if self.instance_ids: # use existing instances
            self.existing_instances = True
            self.instances = self.ec2.instances.filter(InstanceIds=[self.instance_ids[0]])
        
        elif self.dev: # use development instances
            development_instances = [instance for instance in self.ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': ['%s' % MANTRA_DEVELOPMENT_TAG_NAME]}])]

            if development_instances:
                self.instances = self.ec2.instances.filter(InstanceIds=[development_instances[0].id])    
            else:
                self.create_instance()

            self.existing_instances = True

        else: # create new instances
            self.existing_instances = False
            self.create_instance()

    def run_training_instance(self):
        """
        This method takes the list of training instances, from self.instances, and ensures they are running before we SSH into them.

        As of now, this works with a single GPU instance. For the future, and distributed training, we can imagine
        modifying this to work with many.

        From this method we obtain the public DNS (self.public_dns) that we can SSH into.
        """

        try:
            self.active_instance = list(self.instances)[0]
        except IndexError:
            print(colored(' \033[1m [X]', 'red') + colored(' Could not find EC2 Instances', 'red'))

        if self.active_instance.state['Name'] != 'running':
            self.ec2.instances.filter(InstanceIds=[self.active_instance.id]).start()
            self.active_instance.wait_until_running()
            self.active_instance = list(self.ec2.instances.filter(InstanceIds=[self.active_instance.id]))[0]
            time.sleep(2)

        self.public_dns = self.active_instance.public_dns_name

        if not self.public_dns:
            raise ValueError(colored(' \033[1m [X]', 'red') + colored(' Your instance has no public DNS! Please ensure the instance is running.\n', 'red'))

    def s3_to_servers(self, args, execute=True):
        """
        This method moves the data files from S3 to the GPU servers

        Parameters
        -----------

        args : list
            Optional arguments that were used for training

        execute : bool
            If True, executes; else returns a string (useful for testing)

        Returns
        -----------
        void - setups the instance with the appropriate data; else returns a string with the command
        """

        data_dir = 'data/%s' % args.dataset
        s3_command = "cd %s; sudo aws s3 --exact-timestamps sync s3://%s/%s %s/" % (self.project_name, self.settings.S3_BUCKET_NAME, data_dir, data_dir)

        print(colored(' \033[1m [-]', 'white') + colored(' Sending data to instances', 'white'))

        if execute:
            stdin, stdout, stderr = self.client.exec_command(s3_command)
        else:
            return s3_command

        for line in stdout:
            print(line.rstrip()) 

        print(colored(' \033[1m [+]', 'green') + colored(' Data exported to instances', 'white'))

    def send_sh_file_to_instances(self, args, arg_str, execute=True):
        """
        This configures the .sh file that we use to run training on the instance. The SH file contains virtual environment activation,
        pip installation of Python libraries, installing mantraml, and then training.

        Parameters
        -----------
        args : Namespace
            Optional arguments that were used for training

        arg_str - str
            E.g. "--dropout 0.5 --cloud"

        execute : bool
            If True, executes, else returns a string with the contents of the script.sh file

        Returns
        -----------
        void - setups the instance with the .sh file
        """

        if args.verbose:
            if hasattr(args, 'task'):
                sh_script = DEFAULT_SH_TASK_SCRIPT_VERBOSE % (args.model_name, args.dataset, args.task, arg_str)
            else:
                sh_script = DEFAULT_SH_SCRIPT_VERBOSE % (args.model_name, args.dataset, arg_str)
        else:
            if hasattr(args, 'task'):
                sh_script = DEFAULT_SH_TASK_SCRIPT % (args.model_name, args.dataset, args.task, arg_str)
            else:
                sh_script = DEFAULT_SH_SCRIPT % (args.model_name, args.dataset, arg_str)

        if execute:
            stdin, stdout, stderr = self.client.exec_command('cd %s; echo "%s" > script.sh' % (self.project_name, sh_script))
        else:
            return sh_script

        if args.verbose:
            for line in stdout:
                 print(line.rstrip()) 
               
        print(colored(' \033[1m [+]', 'green') + colored(' Instance setup complete', 'white'))

    def setup(self, args, **kwargs):
        """
        This setup method moves project files to S3 and the instances via SCP and then configures the instances with dependencies such as the Mantra library

        Parameters
        -----------
        args : Namespace
            Optional arguments that were used for training

        Returns
        -----------
        void - setups the instance with the appropriate environment and files
        """
        
        self.setup_aws_credentials()
        self.version_artefacts(args, **kwargs)
        self.export_data_to_s3(args)
        self.export_project_files_to_instances()
        self.s3_to_servers(args)

        arg_str, arg_dict = self.configure_arguments(args, **kwargs)
        self.configure_trial_metadata(args=args, arg_dict=arg_dict)
        self.send_sh_file_to_instances(args=args, arg_str=arg_str)

    def setup_aws_credentials(self, execute=True):
        """
        This method configures the AWS credentials on the instance so we can send files to/from the instance to S3

        Parameters
        -----------
        execute : bool
            If True will execute the commands, else will return the credentials file and config file

        Returns
        -----------
        void - versions the artefacts 
        """

        credentials_file = '[default]\naws_access_key_id = %s\naws_secret_access_key = %s' % (self.settings.AWS_ACCESS_KEY_ID, self.settings.AWS_SECRET_ACCESS_KEY)
        config_file = '[default]\nregion=%s' % (self.settings.AWS_DEFAULT_REGION)

        if execute:
            self.client.exec_command('mkdir -p ~/.aws')
            self.client.exec_command('cd ~/.aws; echo "%s" > credentials' % credentials_file)
            self.client.exec_command('cd ~/.aws; echo "%s" > config' % config_file)
        else:
            return credentials_file, config_file

    def train(self, args):
        """
        This method performs training on the cloud; it occurs after setup (once the files have been moved and dependencies installed)

        Parameters
        -----------

        args : dict
            Optional arguments that were used for training
        """

        print(colored('\n \033[1m Training\n', 'blue'))

        stdin, stdout, stderr = self.client.exec_command('cd %s; source script.sh' % self.project_name, get_pty=True)

        for line in stdout:
            output = line.rstrip()
            self.get_training_data_from_s3(output)
            print(output)    

        errors = stderr.read().decode('utf-8')

        if errors:
            print(colored(' \033[1m [X]', 'red') + colored(' Problem encountered while training...', 'red'))
            print(errors) 
            return

        print(colored(' \033[1m [+]', 'green') + colored(' Training complete; now sending model weights to your machine.', 'white'))
        time.sleep(2) # sleep for a bit; catches if a previous sync process is still running
        self.get_training_data_from_s3(output, send_weights=True, force=True)

        if not self.dev:
            print(colored(' \033[1m [.]', 'white') + colored(' Now terminating the GPU instances', 'white'))
            self.active_instance.terminate()
            print(colored(' \033[1m [+]', 'green') + colored(' GPU instances terminated.', 'white'))

    def version_artefact(self, args, artefact_type='MODELS', **kwargs):
        """
        This method versions an artefacts used in the training: data, models tasks. We store to the .mantra folder - it means that we retrieve
        a hash for each artefact that we can record for the user in the UI; and also allows the user to retrieve old model
        or dataset versions on their local at any time.

        Parameters
        -----------
        args : dict
            Optional arguments that were used for training

        artefact_type : str
            Specifies the type of DMT artefact (data-model-task)

        Returns
        -----------
        str - string to display to user containing the hashed artefact
        """

        if artefact_type == 'MODELS':
            folder_name = 'models'
            artefact_name = args.model_name
        elif artefact_type == 'DATA':
            folder_name = 'data'
            artefact_name = args.dataset
        elif artefact_type == 'TASKS':
            folder_name = 'tasks'
            artefact_name = args.task

        artefact_dir = '%s/%s/%s' % (os.getcwd(), folder_name, artefact_name)
        artefact_hash, artefact_hash_dict = MantraHashed.get_folder_hash(folder_dir=artefact_dir)
        
        is_new_artefact = MantraHashed.save_artefact(
            cwd=os.getcwd(), 
            hash=artefact_hash, 
            objects=artefact_hash_dict, 
            args=args, 
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

    def version_artefacts(self, args, **kwargs):
        """
        This method versions the artefacts used in the training: data, models tasks. We store to the .mantra folder - it means that we retrieve
        a hash for each artefact that we can record for the user in the UI; and also allows the user to retrieve old model
        or dataset versions on their local at any time.

        Parameters
        -----------
        args : dict
            Optional arguments that were used for training

        Returns
        -----------
        void - versions the artefacts 
        """

        model_hash_text = self.version_artefact(args=args, artefact_type='MODELS', **kwargs)
        data_hash_text = self.version_artefact(args=args, artefact_type='DATA', **kwargs)
        if args.task:
            task_hash_text = self.version_artefact(args=args, artefact_type='TASKS', **kwargs)

        print(colored(' \033[1m [+]', 'green') + colored(' Model, data and task artefacts versioned', 'white'))

        print(model_hash_text)
        print(data_hash_text)
        if args.task:
            print(task_hash_text)


class S3ProgressPercentage:

    def __init__(self, filename):
        self._filename = filename
        self._size = float(os.path.getsize(filename))
        self._seen_so_far = 0
        self._lock = threading.Lock()

    def __call__(self, bytes_amount):
        with self._lock:
            self._seen_so_far += bytes_amount
            percentage = (self._seen_so_far / self._size) * 100
            sys.stdout.write(
                "\r Uploading %s  %s / %s  (%.2f%%)" % (
                    self._filename, self._seen_so_far, self._size,
                    percentage))
            sys.stdout.flush()
