import boto3
import shutil

from django.db import models

from .consts import MANTRA_DEVELOPMENT_TAG_NAME
from .forms import StartInstanceForm, StopInstanceForm, TerminateInstanceForm

# Create your models here.

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