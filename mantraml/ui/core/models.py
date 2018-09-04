import boto3
from collections import Counter
import datetime
import os
import shutil
import yaml

from django.db import models

from .consts import MANTRA_DEVELOPMENT_TAG_NAME
from .mantra import Mantra
from .forms import StartInstanceForm, StopInstanceForm, TerminateInstanceForm


class Cloud:

    @classmethod
    def change_instance_state(cls, ec2_resource, POST):
        """
        This method changes the state of an instance based on the request of an instance form view.

        Parameters
        ------------

        ec2_resource - boto3.resource('ec2') instance
            The EC2 connection

        POST - request.POST object
            Containing the form information
        """

        if 'stop_instance_id' in POST.dict():
            posted_form = StopInstanceForm(POST)
            if posted_form.is_valid():
                instance_id = posted_form.cleaned_data['stop_instance_id']
                ec2_resource.instances.filter(InstanceIds=[instance_id]).stop()
        elif 'start_instance_id' in POST.dict():
            posted_form = StartInstanceForm(POST)
            if posted_form.is_valid():
                instance_id = posted_form.cleaned_data['start_instance_id']
                ec2_resource.instances.filter(InstanceIds=[instance_id]).start()
        else:
            posted_form = TerminateInstanceForm(POST)
            if posted_form.is_valid():
                instance_id = posted_form.cleaned_data['terminate_instance_id']
                ec2_resource.instances.filter(InstanceIds=[instance_id]).terminate()

    @classmethod
    def get_instance_metadata(cls, instances, no_dev=False):
        """
        This method obtains instance metadata from a list of instances

        Parameters
        ------------

        instances - ec2.instances.filter object
            EC2 instance filter

        no_dev - bool
            If True, excludes development instances.

        Returns
        ------------
        list of dicts - list of instance metadata
        """

        instance_data = []

        for instance in instances:
            instance_dict = {}

            if instance.tags:
                instance_dict['name'] = instance.tags[0]['Value']
            else:
                instance_dict['name'] = ''

            instance_dict['type'] = instance.instance_type
            instance_dict['id'] = instance.id
            instance_dict['tags'] = []
            instance_dict['state'] = instance.state['Name']
            instance_dict['launch_time'] = instance.launch_time

            if no_dev:
                if instance_dict['name'] != MANTRA_DEVELOPMENT_TAG_NAME:
                    instance_data.append(instance_dict)
            else:
                if instance_dict['name'] == MANTRA_DEVELOPMENT_TAG_NAME:
                    instance_dict['tags'] += ['development']
                instance_data.append(instance_dict)

        return instance_data


class Trial:

    column_names = ['timestamp', 'folder_name', 'trial_hash', 'trial_group_hash', 'model_name', 'model_hash', 'data_name', 'data_hash', 'task_name', 'task_hash']

    @classmethod
    def get_trial_contents(cls, settings):
        """
        This method opens the TRIALS metadata file in the .mantra folder and obtains each row of trial metadata

        Parameters
        ------------

        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant

        Returns
        ------------

        list - list of trials each being a list of metadata (str format)
        """
        trial_information = open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, 'r').read()
        return [line.split(" ") for line in trial_information.split("\n") if line]

    @classmethod
    def get_trial_contents_as_dicts(cls, settings):
        """
        This method opens the TRIALS metadata file in the .mantra folder and obtains each row of trial metadata.
        It then converts this data into a list of dictionaries, where the keys come from Trial.column_names

        Parameters
        ------------

        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant

        Returns
        ------------

        list of dicts - each dictionary containing keys (cls.column_names) and values (from the file)
        """
        
        trial_contents = cls.get_trial_contents(settings=settings)
        return [dict(zip(cls.column_names, content)) for content in trial_contents]

    @classmethod
    def remove_group_hash_from_contents(cls, settings, trial_group_hash):
        """
        This method takes a trial contents object - a list of metadata - and removes rows where the group trial hash == trial_group_hash

        Parameters
        ------------
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant

        group_trial_hash - str
            The hash of a group trial
        """

        trial_contents = cls.get_trial_contents(settings=settings)

        new_contents = [trial for trial in trial_contents if not trial[3] == trial_group_hash]
        trial_folder_names = [trial[1] for trial in trial_contents if trial[3] == trial_group_hash]
        new_information = '\n'.join([" ".join(content) for content in new_contents]) + '\n'

        for trial_folder in trial_folder_names:
            shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder)) # delete the trial folder
        
        with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
            trial_file.write(new_information)

    @classmethod
    def get_trial_group_members(cls, settings, model_filter=None, data_filter=None):
        """
        This method takes a trial contents object - a list of metadata - and removes rows where the group trial hash == trial_group_hash

        Parameters
        ------------
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant
    
        model_filter - None or str
            If str, will filter the trials so that the trial['model_name'] == model_filter

        data_filter - None or str
            If str, will filter the trials so that the trial['data_name'] == data_filter

        Returns
        ------------
        dict - key is a trial group hash, value is a list of trials (dict metadata) that correspond to that trial group hash
        list - of trials
        """
        
        trials = cls.get_trial_contents_as_dicts(settings=settings)

        if model_filter:
            trials = [trial for trial in trials if trial['model_name'] == model_filter]
        elif data_filter:
            trials = [trial for trial in trials if trial['data_name'] == data_filter]

        trial_group_hashs = list(set([model['trial_group_hash'] for model in trials]))
        
        trial_group_dict = {trial_group_hash: [trial for trial in trials if trial['trial_group_hash'] == trial_group_hash] for trial_group_hash in trial_group_hashs}

        return trial_group_dict, trials

    @classmethod
    def get_trial_group_name_dict(cls, settings):
        """
        This method retrieves a dictionary with keys as trial group names, and values as string names for these ids. E.g.:

        {'ae42j2ff42f2jeduj4': 'Dropout Experiments'}

        This allows for trial groups to be named with human names, rather than dehumanising SHA-256 hashes.

        Parameters
        ------------
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant

        Returns
        ------------
        dict - key is a trial group hash, value is a name for the trial group e.g. "Learning Rate Tests"
        """

        with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

            yaml_content = yaml.load(trial_group_name_file)

            if not yaml_content:
                yaml_content = {}

        return yaml_content

    @staticmethod
    def get_trial_group_name(trial_group_name_dict, trial_group_hash):
        """
        Parameters
        ------------
        trial_group_name_dict - dict
            The dictionary containing as keys trial group hashes, and as values trial group names, e.g. "Dropout Experiments"

        trial_group_hash - str
            The string for the trial group hash, e.g. a93idjj4v2ojf42of24cew...
        
        Returns
        ------------
        str - the name of the trial group given the dictionary and the hash entered
        """

        try:
            return trial_group_name_dict[trial_group_hash]
        except KeyError:
            return 'Trial Group ' + trial_group_hash[:6]

    @classmethod
    def get_trial_group_metadata(cls, settings, hash, trial_groups):
        """
        This method obtains trial group metadata from a list of trial group dictionaries

        Parameters
        ------------
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant
    
        hash - str
            The hash for the trial group

        trial_groups - list
            List of dicts, where each dict contains metadata on a trial

        Returns
        ------------
        dict - containing metadata on the trial group
        """

        yaml_content = Trial.get_trial_group_name_dict(settings=settings)

        latest_trial_time = datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_groups]))))

        trial_group_metadata = {}

        if not trial_groups:
            return trial_group_metadata
        
        example_trial = trial_groups[0]

        for metadata_name in ['trial_group_hash', 'folder_name', 'model_name', 'model_hash', 'data_name', 'task_name', 'task_hash', 'data_hash']:
            trial_group_metadata[metadata_name] = example_trial[metadata_name]

        dataset_metadata = Mantra.find_dataset_metadata(example_trial['data_name'])
        task_metadata = Mantra.find_task_metadata(example_trial['task_name'])

        trial_group_metadata['time'] = latest_trial_time
        trial_group_metadata['model_metadata'] = Mantra.find_model_metadata(trial_group_metadata['model_name'])
        trial_group_metadata['trial_group_name'] = Trial.get_trial_group_name(yaml_content, example_trial['trial_group_hash'])
        trial_group_metadata['latest_media'] = Mantra.find_latest_trial_media(trial_group_metadata['folder_name'])
        trial_group_metadata['data_full_name'] = dataset_metadata['name']
        trial_group_metadata['task_full_name'] = task_metadata['name']
        trial_group_metadata['data_image'] = dataset_metadata['data_image']
        trial_group_metadata['n_trials'] = len(trial_groups)

        return trial_group_metadata

    @classmethod
    def get_all_trial_group_metadata(cls, settings, trial_group_members):
        """
        This method obtains trial group metadata from a dictionary containing core trial group metadata 

        Parameters
        ------------
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant
    
        trial_group_members - dict
            Keys are trial group hashes; values are list of trial dictionaries corresponding to that trial group

        Returns
        ------------
        list of dicts - each containing metadata on the trial group
        """

        return [cls.get_trial_group_metadata(
            settings=settings, 
            hash=trial_group_hash, 
            trial_groups=trial_groups) for trial_group_hash, trial_groups in trial_group_members.items()]


class Artefact:

    @classmethod
    def all(cls, settings, artefacts_folder):
        """
        This method obtains a list of all artefacts in the artefact folder provided

        Parameters
        ------------
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant
    
        artefacts_folder -
            Path of the folder where the artefact folders are located

        Returns
        ------------
        list of strs - the name of each artefact found in the artefacts_folder path
        """

        artefacts_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, artefacts_folder)

        if os.path.isdir(artefacts_dir):
            artefacts_list = [o for o in os.listdir(artefacts_dir) if os.path.isdir(os.path.join(artefacts_dir, o))]
        else:
            artefacts_list = []

        return artefacts_list


class Task:

    @classmethod
    def calculate_task_metadata(cls, settings, trials):
        """
        This method produces a dictionary of tasks, with keys as the task names, which contain dictionaries of metadata such as the model  
        with the best loss.

        Parameters
        ------------
        
        settings - django.settings file
            Containing information like the MANTRA_PROJECT_ROOT constant
    
        trials - list of dicts
            Each dictionary containing trial metadata

        Returns
        ------------
        dict - keys as task names, values as dictionaries containing metadata on each task
        """

        tasks_used = [trial['task_name'] for trial in trials if trial['task_name'] != 'none']
        occur = Counter(tasks_used)
        task_dict = dict(occur) # e.g. {'task_1': 6} - is a way for us to count the number of trials for each task

        for task_name, n_trials in task_dict.items():
            task_dict[task_name] = {'n_trials': n_trials}
            task_dict[task_name].update(Mantra.find_task_metadata(task_name))

            task_trials = [trial for trial in trials if trial['task_name'] == task_name]

            for task_trial in task_trials:
                try:
                    task_trial['trial_metadata'] = yaml.load(open('%s/trials/%s/trial_metadata.yml' % (settings.MANTRA_PROJECT_ROOT, task_trial['folder_name']), 'r').read())
                except: # can't load yaml
                    task_trial['trial_metadata'] = {}

            try:
                trials_with_validation_loss = [trial for trial in task_trials if 'validation_loss' in trial['trial_metadata']]

                task_dict[task_name]['best_loss'] = min([trial['trial_metadata']['validation_loss'] for trial in trials_with_validation_loss])
                task_dict[task_name]['best_model_folder'] = [trial for trial in trials_with_validation_loss if trial['trial_metadata']['validation_loss'] == task_dict[task_name]['best_loss']][0]['model_name']
                task_dict[task_name]['best_model_metadata'] = Mantra.find_model_metadata(task_dict[task_name]['best_model_folder'])
            except AttributeError:
                task_dict[task_name]['best_loss'] = None
                task_dict[task_name]['best_model_folder'] = None
                if task_dict[task_name]['best_model_folder'] is not None:
                    task_dict[task_name]['best_model_metadata'] = Mantra.find_model_metadata(task_dict[task_name]['best_model_folder'])  
                else:
                    task_dict[task_name]['best_model_metadata'] = None 
            except ValueError:
                task_dict[task_name]['best_loss'] = None
                task_dict[task_name]['best_model_folder'] = None
                if task_dict[task_name]['best_model_folder'] is not None:
                    task_dict[task_name]['best_model_metadata'] = Mantra.find_model_metadata(task_dict[task_name]['best_model_folder'])  
                else:
                    task_dict[task_name]['best_model_metadata'] = None

        return task_dict
