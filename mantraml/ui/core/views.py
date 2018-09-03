import boto3
from collections import Counter
import datetime
import os
import shutil
import subprocess
import sys
import time
import yaml

from tensorboard.backend.event_processing.event_accumulator import EventAccumulator

from django.contrib import admin
from django.conf import settings
from django.template.context_processors import csrf
from django.http import Http404, HttpResponse
from django.shortcuts import render, render_to_response

# Create your views here.
from core.mantra import Mantra
from core.code import CodeBase

from .consts import MANTRA_DEVELOPMENT_TAG_NAME
from .forms import DeleteTrialForm, DeleteTrialGroupForm, StartInstanceForm, StopInstanceForm, TerminateInstanceForm
from .models import Cloud, Trial

def index(request):
    """
    Landing page for the Mantra UI
    """
    config = Mantra.get_config()

    context = {
        "project_name": config["project_name"],
        "models": Mantra.get_models(),
        "datasets": Mantra.get_datasets(),
    }

    return render(request, "index.html", context)

def cloud(request):
    """
    Contains informations on instances that are currently running and allows the user to change the instance state
    (starting, shutting down or terminating)
    """

    ec2 = boto3.resource('ec2')

    if request.method == 'POST':
        Cloud.change_instance_state(ec2_resource=ec2, POST=request.POST)

    start_instance_form = StartInstanceForm()
    stop_instance_form = StopInstanceForm()
    terminate_instance_form = TerminateInstanceForm()

    running_instances = ec2.instances.filter(Filters=[{'Name': 'instance-state-name', 'Values': ['running']}])
    development_instances = ec2.instances.filter(Filters=[{'Name': 'tag:Name', 'Values': ['%s' % MANTRA_DEVELOPMENT_TAG_NAME]}])

    instance_data = Cloud.get_instance_metadata(running_instances, no_dev=True)
    instance_data = instance_data + Cloud.get_instance_metadata(development_instances, no_dev=False)

    return render(request, "cloud.html", {'instance_data': instance_data, 'stop_instance_form': stop_instance_form, 
        'start_instance_form': start_instance_form, 'terminate_instance_form': terminate_instance_form})

def models(request):
    """
    Lists the models that the user has in their project
    """
    config = Mantra.get_config()

    context = {
        "project_name": config["project_name"],
        "models": Mantra.get_models(limit=False)
    }

    return render(request, "models.html", context)

def datasets(request):
    """
    Lists the models that the user has in their project
    """
    config = Mantra.get_config()

    context = {
        "project_name": config["project_name"],
        "datasets": Mantra.get_datasets(limit=False)
    }

    return render(request, "datasets.html", context)

def trials(request):
    """
    Lists the trials that the user has run in their project
    """

    config = Mantra.get_config()

    context = {
        "project_name": config["project_name"],
    }

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)

        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

    form = DeleteTrialGroupForm()

    sys.path.append(settings.MANTRA_PROJECT_ROOT)
    trial_group_members, _ = Trial.get_trial_group_members(settings=settings)

    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

    def get_trial_group_name(trial_group_hash):
        try:
            return yaml_content[trial_group_hash]
        except:
            return 'Trial Group ' + trial_group_hash[:6]

    context['trial_groups'] = [{
    'time': datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_group_value])))),
    'trial_group_hash': trial_group_value[0]['trial_group_hash'],
    'model_name': trial_group_value[0]['model_name'],
    'model_metadata': Mantra.find_model_metadata(trial_group_value[0]['model_name']),
    'model_hash': trial_group_value[0]['model_hash'],
    'data_name': trial_group_value[0]['data_name'],
    'task_name': trial_group_value[0]['task_name'],
    'task_hash': trial_group_value[0]['task_hash'],
    'trial_group_name': get_trial_group_name(trial_group_value[0]['trial_group_hash']),
    'latest_media': Mantra.find_latest_trial_media(trial_group_value[0]['folder_name']),
    'data_full_name': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['name'],
    'task_full_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['name'],
    'data_image': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['data_image'],
    'n_trials': len(trial_group_value),
    'data_hash': trial_group_value[0]['data_hash']} for trial_group_hash, trial_group_value in trial_group_members.items()]
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    context['form'] = form
    
    return render(request, "trials.html", context)

def view_model(request, model_name):
    """
    This view shows the main repository page
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)
        if form.is_valid():

            trial_contents = Trial.get_trial_contents(settings=settings)
            trial_group_hash = form.cleaned_data['trial_group_hash']
            new_contents = [trial for trial in trial_contents if not trial[3] == trial_group_hash]
            trial_folder_names = [trial[1] for trial in trial_contents if trial[3] == trial_group_hash]
            new_information = '\n'.join([" ".join(content) for content in new_contents]) + '\n'

            for trial_folder in trial_folder_names:
                shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder)) # delete the trial folder
            
            with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
                trial_file.write(new_information)

    form = DeleteTrialGroupForm()

    config = Mantra.get_config()
    models_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["models_folder"])
    
    if os.path.isdir(models_dir):
        models_list = [o for o in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, o))]
    else:
        models_list = []

    if model_name not in models_list:
        raise Http404("Model does not exist")

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/models/%s' % (settings.MANTRA_PROJECT_ROOT, model_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars = {**Mantra.find_model_metadata(model_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    request_vars['files'] = CodeBase.get_files('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))
    request_vars['directories'] = CodeBase.get_directories('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))

    trial_group_members, _ = Trial.get_trial_group_members(settings=settings, model_filter=model_name)

    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

    def get_trial_group_name(trial_group_hash):
        try:
            return yaml_content[trial_group_hash]
        except:
            return 'Trial Group ' + trial_group_hash[:6]

    request_vars['trial_groups'] = [{
    'time': datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_group_value])))),
    'trial_group_hash': trial_group_value[0]['trial_group_hash'],
    'trial_group_name': get_trial_group_name(trial_group_value[0]['trial_group_hash']),
    'model_name': trial_group_value[0]['model_name'],
    'model_hash': trial_group_value[0]['model_hash'],
    'data_name': trial_group_value[0]['data_name'],
    'task_name': trial_group_value[0]['task_name'],
    'task_hash': trial_group_value[0]['task_hash'],
    'latest_media': Mantra.find_latest_trial_media(trial_group_value[0]['folder_name']),
    'data_full_name': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['name'],
    'task_full_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['name'],
    'data_image': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['data_image'],
    'n_trials': len(trial_group_value),
    'data_hash': trial_group_value[0]['data_hash']} for trial_group_hash, trial_group_value in trial_group_members.items()]
    request_vars['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    request_vars['form'] = form

    return render(request, 'view_model.html', request_vars)

def view_dataset(request, dataset_name):
    """
    This view shows the dataset module page
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)
        if form.is_valid():

            trial_contents = Trial.get_trial_contents(settings=settings)
            trial_group_hash = form.cleaned_data['trial_group_hash']
            new_contents = [trial for trial in trial_contents if not trial[3] == trial_group_hash]
            trial_folder_names = [trial[1] for trial in trial_contents if trial[3] == trial_group_hash]
            new_information = '\n'.join([" ".join(content) for content in new_contents]) + '\n'

            for trial_folder in trial_folder_names:
                shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder)) # delete the trial folder
            
            with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
                trial_file.write(new_information)

    form = DeleteTrialGroupForm()

    config = Mantra.get_config()
    dataset_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["data_folder"])
    
    if os.path.isdir(dataset_dir):
        dataset_list = [o for o in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, o))]
    else:
        dataset_list = []

    if dataset_name not in dataset_list:
        raise Http404("Dataset does not exist")

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/data/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars = {**Mantra.find_dataset_metadata(dataset_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    request_vars['files'] = CodeBase.get_files('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))
    request_vars['directories'] = CodeBase.get_directories('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, data_filter=dataset_name)

    tasks_used = [model_trial['task_name'] for model_trial in model_trials if model_trial['task_name'] != 'none']
    occur = Counter(tasks_used)
    request_vars['task_list'] = dict(occur)
    for eval_key, eval_val in request_vars['task_list'].items():
        request_vars['task_list'][eval_key] = {'n_trials': eval_val}
        request_vars['task_list'][eval_key].update(Mantra.find_task_metadata(eval_key))

        task_trials = [trial for trial in model_trials if trial['task_name'] == eval_key]

        for task_trial in task_trials:
            try:
                task_trial['trial_metadata'] = yaml.load(open('%s/trials/%s/trial_metadata.yml' % (settings.MANTRA_PROJECT_ROOT, task_trial['folder_name']), 'r').read())
            except: # can't load yaml
                task_trial['trial_metadata'] = {}

        try:
            trials_with_validation_loss = [trial for trial in task_trials if 'validation_loss' in trial['trial_metadata']]

            request_vars['task_list'][eval_key]['best_loss'] = min([trial['trial_metadata']['validation_loss'] for trial in trials_with_validation_loss])
            request_vars['task_list'][eval_key]['best_model_folder'] = [trial for trial in trials_with_validation_loss if trial['trial_metadata']['validation_loss'] == request_vars['task_list'][eval_key]['best_loss']][0]['model_name']
            request_vars['task_list'][eval_key]['best_model_metadata'] = Mantra.find_model_metadata(request_vars['task_list'][eval_key]['best_model_folder'])
        except AttributeError:
            request_vars['task_list'][eval_key]['best_loss'] = None
            request_vars['task_list'][eval_key]['best_model_folder'] = None
            if request_vars['task_list'][eval_key]['best_model_folder'] is not None:
                request_vars['task_list'][eval_key]['best_model_metadata'] = Mantra.find_model_metadata(request_vars['task_list'][eval_key]['best_model_folder'])  
            else:
                request_vars['task_list'][eval_key]['best_model_metadata'] = None 
        except ValueError:
            request_vars['task_list'][eval_key]['best_loss'] = None
            request_vars['task_list'][eval_key]['best_model_folder'] = None
            if request_vars['task_list'][eval_key]['best_model_folder'] is not None:
                request_vars['task_list'][eval_key]['best_model_metadata'] = Mantra.find_model_metadata(request_vars['task_list'][eval_key]['best_model_folder'])  
            else:
                request_vars['task_list'][eval_key]['best_model_metadata'] = None


    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

    def get_trial_group_name(trial_group_hash):
        try:
            return yaml_content[trial_group_hash]
        except:
            return 'Trial Group ' + trial_group_hash[:6]

    request_vars['trial_groups'] = [{
    'time': datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_group_value])))),
    'trial_group_hash': trial_group_value[0]['trial_group_hash'],
    'trial_group_name': get_trial_group_name(trial_group_value[0]['trial_group_hash']),
    'model_name': trial_group_value[0]['model_name'],
    'model_metadata': Mantra.find_model_metadata(trial_group_value[0]['model_name']),
    'model_hash': trial_group_value[0]['model_hash'],
    'data_name': trial_group_value[0]['data_name'],
    'task_name': trial_group_value[0]['task_name'],
    'task_hash': trial_group_value[0]['task_hash'],
    'latest_media': Mantra.find_latest_trial_media(trial_group_value[0]['folder_name']),
    'data_full_name': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['name'],
    'task_full_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['name'],
    'data_image': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['data_image'],
    'n_trials': len(trial_group_value),
    'data_hash': trial_group_value[0]['data_hash']} for trial_group_hash, trial_group_value in trial_group_members.items()]
    request_vars['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    request_vars['form'] = form

    return render(request, 'view_data.html', request_vars)

def view_dataset_codebase(request, dataset_name, path):
    """
    This view shows the dataset module page
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)
        if form.is_valid():

            trial_contents = Trial.get_trial_contents(settings=settings)
            trial_group_hash = form.cleaned_data['trial_group_hash']
            new_contents = [trial for trial in trial_contents if not trial[3] == trial_group_hash]
            trial_folder_names = [trial[1] for trial in trial_contents if trial[3] == trial_group_hash]
            new_information = '\n'.join([" ".join(content) for content in new_contents]) + '\n'

            for trial_folder in trial_folder_names:
                shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder)) # delete the trial folder
            
            with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
                trial_file.write(new_information)

    form = DeleteTrialGroupForm()

    config = Mantra.get_config()
    dataset_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["data_folder"])
    
    if os.path.isdir(dataset_dir):
        dataset_list = [o for o in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, o))]
    else:
        dataset_list = []

    if dataset_name not in dataset_list:
        raise Http404("Dataset does not exist")

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/data/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars = {**Mantra.find_dataset_metadata(dataset_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    request_vars['files'] = CodeBase.get_files('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))
    request_vars['directories'] = CodeBase.get_directories('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, data_filter=dataset_name)

    tasks_used = [model_trial['task_name'] for model_trial in model_trials if model_trial['task_name'] != 'none']
    occur = Counter(tasks_used)
    request_vars['task_list'] = dict(occur)
    for eval_key, eval_val in request_vars['task_list'].items():
        request_vars['task_list'][eval_key] = {'n_trials': eval_val}
        request_vars['task_list'][eval_key].update(Mantra.find_task_metadata(eval_key))

        task_trials = [trial for trial in model_trials if trial['task_name'] == eval_key]

        for task_trial in task_trials:
            try:
                task_trial['trial_metadata'] = yaml.load(open('%s/trials/%s/trial_metadata.yml' % (settings.MANTRA_PROJECT_ROOT, task_trial['folder_name']), 'r').read())
            except: # can't load yaml
                task_trial['trial_metadata'] = {}

        try:
            request_vars['task_list'][eval_key]['best_loss'] = min([trial['trial_metadata']['validation_loss'] for trial in task_trials if 'validation_loss' in trial['trial_metadata']])
            request_vars['task_list'][eval_key]['best_model_folder'] = [trial for trial in task_trials if trial['trial_metadata']['validation_loss'] == request_vars['task_list'][eval_key]['best_loss']][0]['model_name']
            request_vars['task_list'][eval_key]['best_model_metadata'] = Mantra.find_model_metadata(request_vars['task_list'][eval_key]['best_model_folder'])
        except AttributeError:
            request_vars['task_list'][eval_key]['best_loss'] = None
            request_vars['task_list'][eval_key]['best_model_folder'] = None
            if request_vars['task_list'][eval_key]['best_model_folder'] is not None:
                request_vars['task_list'][eval_key]['best_model_metadata'] = Mantra.find_model_metadata(request_vars['task_list'][eval_key]['best_model_folder'])  
            else:
                request_vars['task_list'][eval_key]['best_model_metadata'] = None
        except ValueError:
            request_vars['task_list'][eval_key]['best_loss'] = None
            request_vars['task_list'][eval_key]['best_model_folder'] = None
            if request_vars['task_list'][eval_key]['best_model_folder'] is not None:
                request_vars['task_list'][eval_key]['best_model_metadata'] = Mantra.find_model_metadata(request_vars['task_list'][eval_key]['best_model_folder'])  
            else:
                request_vars['task_list'][eval_key]['best_model_metadata'] = None

    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

    def get_trial_group_name(trial_group_hash):
        try:
            return yaml_content[trial_group_hash]
        except:
            return 'Trial Group ' + trial_group_hash[:6]

    request_vars['trial_groups'] = [{
    'time': datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_group_value])))),
    'trial_group_hash': trial_group_value[0]['trial_group_hash'],
    'trial_group_name': get_trial_group_name(trial_group_value[0]['trial_group_hash']),
    'model_name': trial_group_value[0]['model_name'],
    'model_metadata': Mantra.find_model_metadata(trial_group_value[0]['model_name']),
    'model_hash': trial_group_value[0]['model_hash'],
    'data_name': trial_group_value[0]['data_name'],
    'task_name': trial_group_value[0]['task_name'],
    'task_hash': trial_group_value[0]['task_hash'],
    'latest_media': Mantra.find_latest_trial_media(trial_group_value[0]['folder_name']),
    'data_full_name': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['name'],
    'task_full_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['name'],
    'evaluation_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['evaluation_name'],
    'data_image': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['data_image'],
    'n_trials': len(trial_group_value),
    'data_hash': trial_group_value[0]['data_hash']} for trial_group_hash, trial_group_value in trial_group_members.items()]
    request_vars['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    request_vars['form'] = form

    path = path.rstrip('/')
    blob_path = '%s/data/%s/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name, path)

    # File Information
    file_contents, is_folder, file_type = CodeBase.show_file(blob_path)
    file_lines = len(file_contents.split('\n'))
    file_size = sys.getsizeof(file_contents)

    # Project readme
    directories, files = None, None

    if is_folder:
        directories = CodeBase.get_directories('%s/data/%s/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name, path))
        files = CodeBase.get_files('%s/data/%s/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name, path))
        file_extension = ''
    else:
        file_extension = path.split('.')[-1]

    path_list = CodeBase.get_path_list('/%s' % path)

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars.update({'directories': directories, 'files': files, 'is_folder': is_folder,
    'file_size': file_size, 'file_lines': file_lines, 'file_contents': file_contents, 'file_extension': file_extension, 
    'path_list': path_list, 'path': path, 'file_type': file_type})

    return render(request, 'view_data_codebase.html', request_vars)

def view_dataset_task(request, dataset_name, task_name):
    """
    This view shows the dataset module page
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)
        if form.is_valid():

            trial_contents = Trial.get_trial_contents(settings=settings)
            trial_group_hash = form.cleaned_data['trial_group_hash']
            new_contents = [trial for trial in trial_contents if not trial[3] == trial_group_hash]
            trial_folder_names = [trial[1] for trial in trial_contents if trial[3] == trial_group_hash]
            new_information = '\n'.join([" ".join(content) for content in new_contents]) + '\n'

            for trial_folder in trial_folder_names:
                shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder)) # delete the trial folder
            
            with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
                trial_file.write(new_information)

    form = DeleteTrialGroupForm()

    config = Mantra.get_config()
    dataset_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["data_folder"])
    
    if os.path.isdir(dataset_dir):
        dataset_list = [o for o in os.listdir(dataset_dir) if os.path.isdir(os.path.join(dataset_dir, o))]
    else:
        dataset_list = []

    if dataset_name not in dataset_list:
        raise Http404("Dataset does not exist")

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/data/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars = {**Mantra.find_dataset_metadata(dataset_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    request_vars['files'] = CodeBase.get_files('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))
    request_vars['directories'] = CodeBase.get_directories('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, data_filter=dataset_name)

    task_trials = [trial for trial in model_trials if trial['task_name'] == task_name]

    trials_with_metadata = []

    for trial in task_trials:
        trial.update({'time': datetime.datetime.utcfromtimestamp(int(str(trial['timestamp'])))})
        try:
            trial['metadata'] = yaml.load(open('%s/trials/%s/trial_metadata.yml' % (settings.MANTRA_PROJECT_ROOT, trial['folder_name']), 'r').read())
            trial['model_metadata'] = Mantra.find_model_metadata(trial['model_name'])
            if 'validation_loss' in trial['metadata']:
                trials_with_metadata.append(trial)
       
        except: # can't load yaml
            continue

    request_vars['task_trials'] = trials_with_metadata
    request_vars['task_trials'].sort(key=lambda item: item['metadata']['validation_loss'], reverse=False)

    request_vars['task_name'] = task_name
    request_vars['task_metadata'] = Mantra.find_task_metadata(task_name)


    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

    def get_trial_group_name(trial_group_hash):
        try:
            return yaml_content[trial_group_hash]
        except:
            return 'Trial Group ' + trial_group_hash[:6]

    request_vars['trial_groups'] = [{
    'time': datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_group_value])))),
    'trial_group_hash': trial_group_value[0]['trial_group_hash'],
    'trial_group_name': get_trial_group_name(trial_group_value[0]['trial_group_hash']),
    'model_name': trial_group_value[0]['model_name'],
    'model_metadata': Mantra.find_model_metadata(trial_group_value[0]['model_name']),
    'model_hash': trial_group_value[0]['model_hash'],
    'data_name': trial_group_value[0]['data_name'],
    'task_name': trial_group_value[0]['task_name'],
    'task_hash': trial_group_value[0]['task_hash'],
    'latest_media': Mantra.find_latest_trial_media(trial_group_value[0]['folder_name']),
    'data_full_name': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['name'],
    'task_full_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['name'],
    'evaluation_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['evaluation_name'],
    'data_image': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['data_image'],
    'n_trials': len(trial_group_value),
    'data_hash': trial_group_value[0]['data_hash']} for trial_group_hash, trial_group_value in trial_group_members.items()]
    request_vars['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    request_vars['form'] = form

    return render(request, 'view_data_task.html', request_vars)

def view_model_codebase(request, model_name, path):
    """
    This view shows the codebase for a model
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)
        if form.is_valid():

            trial_contents = Trial.get_trial_contents(settings=settings)
            trial_group_hash = form.cleaned_data['trial_group_hash']
            new_contents = [trial for trial in trial_contents if not trial[3] == trial_group_hash]
            trial_folder_names = [trial[1] for trial in trial_contents if trial[3] == trial_group_hash]
            new_information = '\n'.join([" ".join(content) for content in new_contents]) + '\n'

            for trial_folder in trial_folder_names:
                shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder)) # delete the trial folder
            
            with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
                trial_file.write(new_information)

    form = DeleteTrialGroupForm()

    config = Mantra.get_config()
    models_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["models_folder"])
    
    if os.path.isdir(models_dir):
        models_list = [o for o in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, o))]
    else:
        models_list = []

    if model_name not in models_list:
        raise Http404("Model does not exist")

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/models/%s' % (settings.MANTRA_PROJECT_ROOT, model_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars = {**Mantra.find_model_metadata(model_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    request_vars['files'] = CodeBase.get_files('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))
    request_vars['directories'] = CodeBase.get_directories('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, data_filter=model_name)

    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

    def get_trial_group_name(trial_group_hash):
        try:
            return yaml_content[trial_group_hash]
        except:
            return 'Trial Group ' + trial_group_hash[:6]

    request_vars['trial_groups'] = [{
    'time': datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in trial_group_value])))),
    'trial_group_hash': trial_group_value[0]['trial_group_hash'],
    'trial_group_name': get_trial_group_name(trial_group_value[0]['trial_group_hash']),
    'model_name': trial_group_value[0]['model_name'],
    'model_hash': trial_group_value[0]['model_hash'],
    'data_name': trial_group_value[0]['data_name'],
    'task_name': trial_group_value[0]['task_name'],
    'task_hash': trial_group_value[0]['task_hash'],
    'latest_media': Mantra.find_latest_trial_media(trial_group_value[0]['folder_name']),
    'data_full_name': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['name'],
    'task_full_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['name'],
    'evaluation_name': Mantra.find_task_metadata(trial_group_value[0]['task_name'])['evaluation_name'],
    'data_image': Mantra.find_dataset_metadata(trial_group_value[0]['data_name'])['data_image'],
    'n_trials': len(trial_group_value),
    'data_hash': trial_group_value[0]['data_hash']} for trial_group_hash, trial_group_value in trial_group_members.items()]
    request_vars['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    request_vars['form'] = form

    path = path.rstrip('/')
    blob_path = '%s/models/%s/%s' % (settings.MANTRA_PROJECT_ROOT, model_name, path)

    # File Information
    file_contents, is_folder, file_type = CodeBase.show_file(blob_path)
    file_lines = len(file_contents.split('\n'))
    file_size = sys.getsizeof(file_contents)

    directories, files = None, None

    if is_folder:
        directories = CodeBase.get_directories('%s/models/%s/%s'% (settings.MANTRA_PROJECT_ROOT, model_name, path))
        files = CodeBase.get_files('%s/models/%s/%s'% (settings.MANTRA_PROJECT_ROOT, model_name, path))
        file_extension = ''
    else:
        file_extension = path.split('.')[-1]

    path_list = CodeBase.get_path_list('/%s' % path)

    request_vars.update({'directories': directories, 'files': files, 'is_folder': is_folder,
    'file_size': file_size, 'file_lines': file_lines, 'file_contents': file_contents, 'file_extension': file_extension, 
    'path_list': path_list, 'path': path, 'file_type': file_type})

    return render(request, 'view_codebase.html', request_vars)

def view_trial_group(request, trial_group_folder):
    """
    This view shows a group of trials for a given trial id
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialForm(request.POST)
        if form.is_valid():

            trials = Trial.get_trial_contents_as_dicts(settings=settings)
            group_trials =  [group_trial for group_trial in trials if group_trial['trial_group_hash'].startswith(trial_group_folder)]

            trial_hash = form.cleaned_data['trial_hash']
            new_contents = [trial for trial in trial_contents if not trial[2] == trial_hash]

            try:
                trial_folder_name = [trial for trial in trial_contents if trial[2] == trial_hash][0][1]
                trial_exists = True
            except IndexError:
                trial_exists = False

            if trial_exists:

                new_information =  '\n'.join([" ".join(content) for content in new_contents]) + '\n'

                if os.path.exists('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder_name)):
                    shutil.rmtree('%s/%s/%s' % (settings.MANTRA_PROJECT_ROOT, 'trials', trial_folder_name)) # delete the trial folder
                
                with open("%s/.mantra/TRIALS" % settings.MANTRA_PROJECT_ROOT, "w") as trial_file:
                    trial_file.write(new_information)

    trials = Trial.get_trial_contents_as_dicts(settings=settings)
    group_trials =  [group_trial for group_trial in trials if group_trial['trial_group_hash'].startswith(trial_group_folder)]

    form = DeleteTrialForm()

    if not group_trials:
        raise Http404("Trial Group does not exist")
    else:
        sys.path.append(settings.MANTRA_PROJECT_ROOT)
        model_trials =  [trial for trial in trials if trial['trial_group_hash'] == group_trials[0]['trial_group_hash']]
        task_name = model_trials[0]['task_name']
        task_full_name = Mantra.find_task_metadata(task_name)['name']
        evaluation_name = Mantra.find_task_metadata(task_name)['evaluation_name']

    request_vars = {}

    with open("%s/.mantra/TRIAL_GROUP_NAMES" % settings.MANTRA_PROJECT_ROOT, "r") as trial_group_name_file:

        yaml_content = yaml.load(trial_group_name_file)

        if not yaml_content:
            yaml_content = {}

        try:
            request_vars['trial_group_name'] = yaml_content[model_trials[0]['trial_group_hash']]
        except:
            request_vars['trial_group_name'] = 'Trial Group ' + model_trials[0]['trial_group_hash'][:6]


    request_vars['task_name'] = task_name
    request_vars['task_full_name'] = task_full_name
    request_vars['evaluation_name'] = evaluation_name
    request_vars['trial_group_hash'] = model_trials[0]['trial_group_hash']
    request_vars['trials'] = model_trials
    request_vars['latest_trial'] = datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in model_trials]))))

    hyperparameter_list = []
    metric_name_list = []

    for trial in request_vars['trials']:
        trial.update({'time': datetime.datetime.utcfromtimestamp(int(str(trial['timestamp'])))})
        try:
            trial['metadata'] = yaml.load(open('%s/trials/%s/trial_metadata.yml' % (settings.MANTRA_PROJECT_ROOT, trial['folder_name']), 'r').read())
        except: # can't load yaml
            trial['metadata'] = {}

        if 'hyperparameters' in trial['metadata']:
            hyperparameter_list = hyperparameter_list + list(trial['metadata']['hyperparameters'].keys())
        
        if 'secondary_metrics' in trial['metadata']:
            metric_name_list = metric_name_list + list(trial['metadata']['secondary_metrics'].keys())

    occur = Counter([hyperparm for hyperparm in hyperparameter_list if hyperparm != 'epochs'])
    request_vars['hyperparms'] = [i[0] for i in occur.most_common(5)]
    request_vars['metric_names'] = list(set(metric_name_list))

    for trial in request_vars['trials']:
        if 'hyperparameters' in trial['metadata']:
            hyperparm_list = []
            for hyperparm_no, hyperparm in enumerate(request_vars['hyperparms']):
                if hyperparm in trial['metadata']['hyperparameters']:

                    hyperparameter_value = trial['metadata']['hyperparameters'][hyperparm]

                    if isinstance(hyperparameter_value, list):
                        hyperparameter_value_type = 'list'
                    elif isinstance(hyperparameter_value, float):
                        hyperparameter_value_type = 'float'
                    else:
                        hyperparameter_value_type = 'str'

                    hyperparm_list.append({'value': hyperparameter_value, 'type': hyperparameter_value_type})
                else:
                    hyperparm_list.append({})

            trial.update({'hyperparm_values': hyperparm_list})
        else:
            trial.update({'hyperparm_values': [None]*len(request_vars['hyperparms'])})

        if 'secondary_metrics' in trial['metadata']:
            metric_list = []
            for metric_no, metric in enumerate(request_vars['metric_names']):
                if metric in trial['metadata']['secondary_metrics']:
                    metric_list.append(trial['metadata']['secondary_metrics'][metric])
                else:
                    metric_list.append(None)

            trial.update({'metric_values': metric_list})
        else:
            trial.update({'metric_values': [None]*len(request_vars['metric_names'])})

    request_vars['hyperparms'] = [hyperparm.replace('_', ' ').title() for hyperparm in request_vars['hyperparms']]

    request_vars['trials'].sort(key=lambda item: item['time'], reverse=True)

    request_vars['model'] = {}
    request_vars['data'] = {}
    request_vars['model'].update(Mantra.find_model_metadata(model_trials[0]['model_name']))
    request_vars['data'].update(Mantra.find_dataset_metadata(model_trials[0]['data_name']))
    request_vars['form'] = form 

    return render(request, 'view_trial_group.html', request_vars)

def view_trial(request, trial_folder):
    """
    This view shows an individual trial
    """

    trials = Trial.get_trial_contents_as_dicts(settings=settings)
    model_trials =  [trial for trial in trials if trial_folder in trial['folder_name']]

    if not model_trials:
        raise Http404("Poll does not exist")
    else:
        model_trial = model_trials[0]
        trial_folder_name = model_trials[0]['folder_name']

    event_acc = EventAccumulator('%s/trials/%s/logs' % (settings.MANTRA_PROJECT_ROOT, trial_folder_name))
    event_acc.Reload()

    scalars = list(event_acc.scalars._buckets.keys())

    scalar_values = {}
    for scalar in scalars:
        scalar_values[scalar] = {}
        scalar_values[scalar]['time'] = [item[0] for item in event_acc.Scalars(scalar)]
        scalar_values[scalar]['steps'] = [str(i) for i in range(len(scalar_values[scalar]['time']))]
        scalar_values[scalar]['values'] = [item[2] for item in event_acc.Scalars(scalar)]

    request_vars = {}
    request_vars['scalars'] = scalar_values
    request_vars['latest_media'] = Mantra.find_latest_trial_media(trial_folder_name)

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    request_vars['model'] = {}
    request_vars['data'] = {}

    request_vars['model'].update(Mantra.find_model_metadata(model_trial['model_name']))
    request_vars['data'].update(Mantra.find_dataset_metadata(model_trial['data_name']))

    return render(request, 'view_trial.html', request_vars)

def view_trial_tensorboard(request, trial_folder):
    """
    This view shows an individual trial with tensorboard
    """

    trials = Trial.get_trial_contents_as_dicts(settings=settings)
    model_trials =  [trial for trial in trials if trial_folder in trial['folder_name']]

    if not model_trials:
        raise Http404("Poll does not exist")
    else:
        model_trial = model_trials[0]
        trial_folder_name = model_trials[0]['folder_name']
    
    subprocess.Popen('pkill -f tensorboard', shell=True, stderr=subprocess.DEVNULL)
    path = '%s/trials/%s/logs' % (settings.MANTRA_PROJECT_ROOT, trial_folder_name)
    subprocess.Popen('tensorboard --logdir=' + path, stdout=open(os.devnull, 'wb'), shell=True)
    time.sleep(2)

    return render(request, 'view_trial_tensorboard.html', {})

def console(request):
    """
    A console view
    """

    context = {}
    context.update(csrf(request))

    return render(request, 'console.html', context)

def console_post(request):
    """
    Accepts POST requests from the web console, processes it and returns the result.
    """
    if request.POST:
        command = request.POST.get("command")
        if command:
            try:
                data = subprocess.check_output(command, shell=True, stderr=subprocess.STDOUT)
            except subprocess.CalledProcessError as e:
                data = e.output
            data = data.decode('utf-8')
            output = "%c(@olive)%" + data + "%c()"
        else:
            output = "%c(@orange)%Try `ls` to start with.%c()"
        return HttpResponse(output)
    return HttpResponse("Unauthorized.", status=403)

