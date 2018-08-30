from termcolor import colored
import datetime
import lazy_import
import os
import subprocess
import sys
import time
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


from .consts import DEFAULT_SH_SCRIPT, DEFAULT_SH_SCRIPT_VERBOSE, DEFAULT_SH_TASK_SCRIPT, DEFAULT_SH_TASK_SCRIPT_VERBOSE, MANTRA_DEVELOPMENT_TAG_NAME


class AWS:
    """
    This class contains methods for interacting with AWS : with a focus on the following functionality:

        - Launching new GPU compute instances on the user's request for training
        - Moving Mantra projects to the cloud for training
        - Retrieving the results of training in the cloud and returning them to a local server
    """

    def __init__(self, settings=None, instance_ids=None, dataset_class=None, dev=False, project_name='default'):
        """
        Parameters
        -----------

        settings : Python module
            List of Mantra consts that determines AWS parameters

        instance_ids : list
            If not None, will use provided instances for training - CURRENTLY ONLY TAKES THE FIRST INSTANCE (TODO: DISTRIBUTED TRAINING)

        project_name : str
            The name of the Mantra projects - this string is used for folder creation on the cloud instances; arbitrary.

        dataset_class : Dataset type class
            Representing the Dataset that will be transferred to S3

        dev : bool
            If true, loads up (or creates) a development machine that does not terminate after job completion
        """

        print(colored('\n \033[1m Mantra Training', 'blue') + colored('\033[1m 🚀\n', 'green'))

        print(colored(' \033[1m Setup\n', 'blue'))

        self.settings = settings
        self.dataset_class = dataset_class

        self.ec2 = boto3.resource('ec2')

        if instance_ids: # use existing instances
            self.existing_instances = True
            self.instances = self.ec2.instances.filter(InstanceIds=[instance_ids[0]])
        
        elif dev:
            development_instances = [instance for instance in self.ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': ['%s' % MANTRA_DEVELOPMENT_TAG_NAME]}])]

            if development_instances:
                self.existing_instances = True
                self.instances = self.ec2.instances.filter(InstanceIds=[development_instances[0].id])    
            else:
                self.create_instance(settings, development=True)

        else: # create new instances
            self.existing_instances = False
            self.create_instance(settings)

        instances = [instance for instance in self.instances]
        active_instance = instances[0]

        if active_instance.state['Name'] != 'running':
            self.ec2.instances.filter(InstanceIds=[active_instance.id]).start()
            time.sleep(3)

        self.public_dns = active_instance.public_dns_name

        if not self.public_dns:
            raise ValueError('Your instance has no public DNS! Please ensure they are running.\n')

        self.project_name = project_name

        key = paramiko.RSAKey.from_private_key_file(os.path.expanduser(self.settings.AWS_KEY_PATH))
        self.client = paramiko.SSHClient()
        self.client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self.client.connect(hostname=self.public_dns, username="ubuntu", pkey=key)

        print(colored(' \033[1m [+]', 'green') + colored(' Cloud connection established : using %s GPU instances' % len(instances), 'white'))

    def create_instance(self, settings, development=False):
        """
        This method creates a new AWS instance

        Parameters
        -----------

        settings : Python module
            List of Mantra consts that determines AWS parameters

        development : bool
            If True, tags the new instance with a development tag
        """

        additional_args = {}

        if settings.AWS_SECURITY_GROUP:
            additional_args['SecurityGroupIds'] = [settings.AWS_SECURITY_GROUP]

        print(colored(' \033[1m [-]', 'white') + colored(' Creating a %s instance' % settings.AWS_INSTANCE_TYPE, 'white'))

        instance_ids = self.ec2.create_instances(
            ImageId=settings.AWS_AMI_IMAGE_ID, 
            KeyName=settings.AWS_KEY_PATH.split('/')[-1].replace('.pem', ''), 
            MinCount=1, 
            MaxCount=1, 
            InstanceType=settings.AWS_INSTANCE_TYPE,
            **additional_args)
        self.instances = self.ec2.instances.filter(InstanceIds=[instance_ids[0].id])

        instance = [instance for instance in self.instances][0]
        instance.wait_until_running()

        if development:
            self.ec2.create_tags(Resources=[instance.id], Tags=[{'Key':'Name', 'Value': MANTRA_DEVELOPMENT_TAG_NAME}])

        print(colored(' \033[1m [+]', 'green') + colored(' Instance now running', 'white'))

    @classmethod
    def sync_data(cls, args, settings):
        """
        This method retrieves data from S3 and sends to the user's local machine

        Parameters
        -----------
        args : dict
            Arguments that were used in an Mantra command

        settings : Python module
            List of Mantra consts that determines AWS parameters

        Returns
        -----------
        void - sends files from S3 to local
        """

        if args.artefact == 'trials':
            aws_cmd = 'aws s3 --exact-timestamps sync s3://%s/trials trials' % (settings.S3_BUCKET_NAME)
        elif args.artefact == 'data':
            if input("This will overwrite same-name files in your data directory. Are you sure? (y/n)\n") != "y":
                exit()
            aws_cmd = 'aws s3 --exact-timestamps sync s3://%s/data data' % (settings.S3_BUCKET_NAME)
        
        os.system(aws_cmd)

        print(colored('\n \033[1m [+]', 'green') + colored(' Sync complete\n', 'white'))

    def create_s3_bucket(self, s3_client, s3_buckets):
        """"
        This method creates an S3 Mantra project bucket if the user has not already created it

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

    def export_data_to_s3(self, args):
        """
        This method exports data modules to the user's S3. We check for the existence of an Mantra bucket.
        If it doesn't exist we create one. Then we check for the existence of the user's data - and check the 
        hash. If it is different, we reupload.

        Parameters
        -----------

        args : list
            Optional arguments that were used for training

        Returns
        -----------
        void - setups the instance with the appropriate environment and files
        """

        # Find tar directory
        data_dir = '%s/data/%s/' % (os.getcwd(), args.dataset)
        config_dir = '%sconfig.yml' % data_dir

        # s3 bucket locations
        s3_data_bucket_dir = 'data/%s/raw/' % args.dataset
        s3_data_hash_location = '%shash' % s3_data_bucket_dir

        # Hashing details
        local_hash = self.dataset_class.get_data_folder_hash(data_dir=data_dir, files=self.dataset_class.files)

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

            if s3_hash == local_hash:
                print(colored(' \033[1m [+]', 'green') + colored(' Data exported to S3', 'white'))
                return

        # If the hash is different, or we don't have both files, then upload the dataset to S3
        for file in self.dataset_class.files:
            s3_client.upload_file('%sraw/%s' % (data_dir, file), self.settings.S3_BUCKET_NAME, '%s%s' % (s3_data_bucket_dir, file), 
                Callback=S3ProgressPercentage('%sraw/%s' % (data_dir, file)))

        hash_object.put(Body=local_hash)

        print(colored('\n \033[1m [+]', 'green') + colored(' Data exported to S3', 'white'))

    @classmethod
    def export_trials_to_s3(cls, model):
        """
        This method exports trial data to the user's S3.
        """

        path = '%s/trials/%s/' % (os.getcwd(), model.trial_folder_name)

        # s3 bucket locations
        s3_model_bucket_dir = 'trials/%s/' % model.trial_folder_name

        aws_cmd = 'aws s3 --exact-timestamps sync --quiet %s s3://%s/%s' % (path, model.settings.S3_BUCKET_NAME, s3_model_bucket_dir)
        os.system(aws_cmd)

    def s3_to_servers(self, args):
        """
        This method moves the data files from S3 to the GPU servers

        Parameters
        -----------

        args : list
            Optional arguments that were used for training

        Returns
        -----------
        void - setups the instance with the appropriate data
        """

        data_dir = 'data/%s' % args.dataset
        s3_command = "cd %s; sudo aws s3 --exact-timestamps sync s3://%s/%s %s/" % (self.project_name, self.settings.S3_BUCKET_NAME, data_dir, data_dir)

        print(colored(' \033[1m [-]', 'white') + colored(' Sending data to instances', 'white'))

        stdin, stdout, stderr = self.client.exec_command(s3_command)

        for line in stdout:
            print(line.rstrip()) 

        print(colored(' \033[1m [+]', 'green') + colored(' Data exported to instances', 'white'))

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
        """
        arg_dict = {}
        arg_str = ''

        # First Process the Arguments

        for arg_key, arg_value in args.__dict__.items():
            if arg_value and arg_key not in ['func', 'model_name', 'dataset', 'cloud']:
                if arg_value is True:
                    arg_str += ' --%s' % arg_key
                elif isinstance(arg_value, list):
                    arg_str += ' --%s %s' % (arg_key, ' '.join(arg_value))
                elif arg_value not in [True, False]:
                    arg_str += ' --%s %s' % (arg_key, arg_value)
                    
                arg_dict[arg_key] = arg_value

        # Secondly any Keyword (additional) arguments

        for arg_key, arg_value in kwargs.items():
            if arg_value is True:
                arg_str += ' --%s' % arg_key
            elif arg_value not in [True, False]:
                arg_str += ' --%s %s' % (arg_key, arg_value)
                
                arg_dict[arg_key] = arg_value

        return arg_str, arg_dict

    def configure_trial_metadata(self, args, arg_dict):
        """
        This method configures the trial metadata file

        Parameters
        -----------
        args : Namespace
            Optional arguments that were used for training

        arg_dict : dict
            Containing arguments that were used for training

        Returns
        -----------
        void - creates the metadata yaml and sends it to the instances 
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
            metadata['task_hash'] = ""

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

        stdin, stdout, stderr = self.client.exec_command('cd %s; echo "%s" > trial_metadata.yml' % (self.project_name, yaml_content))

        # Write data to TRIALS file for record keeping

        self.trial_folder_name = '%s_%s_%s_%s' % (metadata['timestamp'], metadata['model_name'], metadata['data_name'], metadata['trial_hash'][:SHORT_HASH_INT])
        f = open('%s/%s' % (os.getcwd(), '.mantra/TRIALS'), "a")
        f.write('%s %s %s %s %s %s %s %s %s %s\n' % (metadata['timestamp'], self.trial_folder_name, metadata['trial_hash'], 
            metadata['trial_group_hash'],
            metadata['model_name'],
            metadata['model_hash'],
            metadata['data_name'],
            metadata['data_hash'],
            metadata['task_name'],
            metadata['task_hash']))
        f.close()

        return True

    def setup(self, args, **kwargs):
        """
        This method moves the files to the cloud via SCP and then configures the environment with dependencies such as the Mantra library

        Parameters
        -----------
        args : Namespace
            Optional arguments that were used for training

        Returns
        -----------
        void - setups the instance with the appropriate environment and files
        """
        
        self.setup_aws_credentials(args, **kwargs)
        self.version_artefacts(args, **kwargs)
        self.export_data_to_s3(args)

        # Move project files
        rsync_string = "rsync -avL --exclude '*.tar.gz' --exclude 'trials/*' --exclude '.extract*' --exclude '.mantra*' --progress -e 'ssh -i %s' %s ubuntu@%s:/home/ubuntu/%s > /dev/null" % (self.settings.AWS_KEY_PATH, './', self.public_dns, self.project_name)
        os.system(rsync_string)
        print(colored(' \033[1m [+]', 'green') + colored(' Project files moved to instances', 'white'))

        self.s3_to_servers(args)

        arg_str, arg_dict = self.configure_arguments(args, **kwargs)
        self.configure_trial_metadata(args, arg_dict)

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

        stdin, stdout, stderr = self.client.exec_command('cd %s; echo "%s" > script.sh' % (self.project_name, sh_script))

        if args.verbose:
            for line in stdout:
                 print(line.rstrip()) 
               
        print(colored(' \033[1m [+]', 'green') + colored(' Dependencies installed on instances', 'white'))

    def setup_aws_credentials(self, args, **kwargs):
        """
        This method configures the aws credentials on the instance

        Parameters
        -----------
        args : dict
            Optional arguments that were used for training

        Returns
        -----------
        void - versions the artefacts 
        """

        credentials_file = '[default]\naws_access_key_id = %s\naws_secret_access_key = %s' % (self.settings.AWS_ACCESS_KEY_ID, self.settings.AWS_SECRET_ACCESS_KEY)
        config_file = '[default]\nregion=%s' % (self.settings.AWS_DEFAULT_REGION)

        stdin, stdout, stderr = self.client.exec_command('mkdir -p ~/.aws')
        stdin, stdout, stderr = self.client.exec_command('cd ~/.aws; echo "%s" > credentials' % credentials_file)
        stdin, stdout, stderr = self.client.exec_command('cd ~/.aws; echo "%s" > config' % config_file)

    def version_artefacts(self, args, **kwargs):
        """
        This method versions the artefacts used in the training. We store to the .mantra folder - it means that we retrieve
        a hash for each artefact that we can record for the user in the UI; and also allows the user to retrieve old model
        or dataset versions on their local at any time

        Parameters
        -----------
        args : dict
            Optional arguments that were used for training

        Returns
        -----------
        void - versions the artefacts 
        """

        model_dir = '%s/models/%s' % (os.getcwd(), args.model_name)
        self.model_hash, ref_table = MantraHashed.get_folder_hash(model_dir)
        new_model = MantraHashed.save_artefact(os.getcwd(), self.model_hash, ref_table, args, artefact_type='MODELS', **kwargs)
        
        model_hash_text = colored(' \033[1m ...', 'white') + colored(' Model hash:        %s' % self.model_hash, 'blue')
        if new_model:
            model_hash_text += colored(' (new)', 'white')

        data_dir = '%s/data/%s' % (os.getcwd(), args.dataset)
        self.data_hash, ref_table = MantraHashed.get_folder_hash(data_dir)
        new_data = MantraHashed.save_artefact(os.getcwd(), self.data_hash, ref_table, args, artefact_type='DATA', **kwargs)
        
        data_hash_text = colored(' \033[1m ...', 'white') + colored(' Data hash:         %s' % self.data_hash, 'blue')
        if new_data:
            data_hash_text += colored(' (new)', 'white')

        if args.task:
            task_dir = '%s/tasks/%s' % (os.getcwd(), args.task)
            self.task_hash, ref_table = MantraHashed.get_folder_hash(task_dir)
            new_task = MantraHashed.save_artefact(os.getcwd(), self.task_hash, ref_table, args, artefact_type='TASKS', **kwargs)
            
            task_hash_text = colored(' \033[1m ...', 'white') + colored(' Task hash:         %s' % self.task_hash, 'blue')
            if new_task:
                task_hash_text += colored(' (new)', 'white')

        print(colored(' \033[1m [+]', 'green') + colored(' Model and data artefacts versioned', 'white'))

        print(model_hash_text)
        print(data_hash_text)
        if args.task:
            print(task_hash_text)

    def get_training_data_from_s3(self, args, output, send_weights=False, force=False):
        """
        This method retrieves training data from S3 and sends to the user's local machine

        Parameters
        -----------
        args : dict
            Optional arguments that were used for training

        output - str
            The latest stdout line from training

        send_weights - bool
            If true, send the model weights from S3 to local

        force : bool
            If force, force the sync (irrespective of content in the stdout)

        Returns
        -----------
        void - sends files from S3 to local
        """
        
        if ('Epoch' in output) or force: # each time we have a new epoch of training, we send the files to local
            if send_weights:    
                aws_cmd = 'aws s3 --quiet --exact-timestamps sync s3://%s/trials/%s trials/%s' % (self.settings.S3_BUCKET_NAME, self.trial_folder_name, self.trial_folder_name)
            else:
                aws_cmd = "aws s3 --quiet --exact-timestamps sync s3://%s/trials/%s trials/%s --exclude 'checkpoint/*'" % (self.settings.S3_BUCKET_NAME, self.trial_folder_name, self.trial_folder_name)

            os.system(aws_cmd)

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
            self.get_training_data_from_s3(args, output)
            print(output)    

        errors = stderr.read().decode('utf-8')

        if errors:
            print(colored(' \033[1m [X]', 'red') + colored(' Problem encountered while training...', 'red'))
            print(errors) 
            return

        print(colored(' \033[1m [+]', 'green') + colored(' Training complete; now sending model weights to your machine.', 'white'))
        time.sleep(2) # sleep for a bit; catches if a previous sync process is still running
        self.get_training_data_from_s3(args, output, send_weights=True, force=True)


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
