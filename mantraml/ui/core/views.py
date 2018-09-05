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
from .models import Artefact, Cloud, Task, Trial

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

    context = {"project_name": config["project_name"]}

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)

        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

    form = DeleteTrialGroupForm()

    sys.path.append(settings.MANTRA_PROJECT_ROOT)
    trial_group_members, _ = Trial.get_trial_group_members(settings=settings)
    context['trial_groups'] = Trial.get_all_trial_group_metadata(settings=settings, trial_group_members=trial_group_members)
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    context['form'] = form
    
    return render(request, "trials.html", context)

def view_model(request, model_name):
    """
    This view displays a model and its various dependencies and metadatas
    """

    config = Mantra.get_config()

    models_list = Artefact.all(settings=settings, artefacts_folder=config['models_folder'])

    if model_name not in models_list:
        raise Http404("Model does not exist")

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)
        
        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

    form = DeleteTrialGroupForm()

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    readme_content, readme_exists = CodeBase.get_readme('%s/models/%s' % (settings.MANTRA_PROJECT_ROOT, model_name))
    context = {**Mantra.find_model_metadata(model_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    context['files'] = CodeBase.get_files('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))
    context['directories'] = CodeBase.get_directories('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))

    trial_group_members, _ = Trial.get_trial_group_members(settings=settings, model_filter=model_name)
    context['trial_groups'] = Trial.get_all_trial_group_metadata(settings=settings, trial_group_members=trial_group_members)
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    context['form'] = form

    return render(request, 'view_model.html', context)

def view_dataset(request, dataset_name):
    """
    This view displays a dataset and its various dependencies and metadatas
    """

    config = Mantra.get_config()

    data_list = Artefact.all(settings=settings, artefacts_folder=config['data_folder'])

    if dataset_name not in data_list:
        raise Http404("Dataset does not exist")

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)

        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

    form = DeleteTrialGroupForm()

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    readme_content, readme_exists = CodeBase.get_readme('%s/data/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name))
    context = {**Mantra.find_dataset_metadata(dataset_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    context['files'] = CodeBase.get_files('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))
    context['directories'] = CodeBase.get_directories('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, data_filter=dataset_name)

    context['task_list'] = Task.calculate_task_metadata(settings=settings, trials=model_trials)
    context['trial_groups'] = Trial.get_all_trial_group_metadata(settings=settings, trial_group_members=trial_group_members)
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    context['form'] = form

    return render(request, 'view_data.html', context)

def view_dataset_codebase(request, dataset_name, path):
    """
    This view displays a dataset codebase and its various dependencies and metadatas
    """

    config = Mantra.get_config()

    data_list = Artefact.all(settings=settings, artefacts_folder=config['data_folder'])

    if dataset_name not in data_list:
        raise Http404("Dataset does not exist")

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)

        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

    form = DeleteTrialGroupForm()

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/data/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    context = {**Mantra.find_dataset_metadata(dataset_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    context['files'] = CodeBase.get_files('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))
    context['directories'] = CodeBase.get_directories('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, data_filter=dataset_name)

    context['task_list'] = Task.calculate_task_metadata(settings=settings, trials=model_trials)
    context['trial_groups'] = Trial.get_all_trial_group_metadata(settings=settings, trial_group_members=trial_group_members)
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    context['form'] = form

    path = path.rstrip('/')

    codebase_data = CodeBase.get_code_data(
        blob_path='%s/data/%s/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name, path),
        path=path)
    context.update(codebase_data)

    return render(request, 'view_data_codebase.html', context)

def view_dataset_task(request, dataset_name, task_name):
    """
    This view shows the dataset module page
    """

    config = Mantra.get_config()

    data_list = Artefact.all(settings=settings, artefacts_folder=config['data_folder'])

    if dataset_name not in data_list:
        raise Http404("Dataset does not exist")

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)

        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

    form = DeleteTrialGroupForm()

    # Project readme
    readme_content, readme_exists = CodeBase.get_readme('%s/data/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name))

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    context = {**Mantra.find_dataset_metadata(dataset_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    context['files'] = CodeBase.get_files('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))
    context['directories'] = CodeBase.get_directories('%s/data/%s'% (settings.MANTRA_PROJECT_ROOT, dataset_name))

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

    context['task_trials'] = trials_with_metadata
    context['task_trials'].sort(key=lambda item: item['metadata']['validation_loss'], reverse=False)

    context['task_name'] = task_name
    context['task_metadata'] = Mantra.find_task_metadata(task_name)
    
    context['trial_groups'] = Trial.get_all_trial_group_metadata(settings=settings, trial_group_members=trial_group_members)
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)
    context['form'] = form

    return render(request, 'view_data_task.html', context)

def view_model_codebase(request, model_name, path):
    """
    This view shows the codebase for a model
    """

    # delete trial option - catch and process
    if request.method == 'POST':
        form = DeleteTrialGroupForm(request.POST)

        if form.is_valid():
            Trial.remove_group_hash_from_contents(settings=settings, trial_group_hash=form.cleaned_data['trial_group_hash'])

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

    context = {**Mantra.find_model_metadata(model_name), 'readme_exists': readme_exists, 'readme_content': readme_content}
    context['files'] = CodeBase.get_files('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))
    context['directories'] = CodeBase.get_directories('%s/models/%s'% (settings.MANTRA_PROJECT_ROOT, model_name))

    trial_group_members, model_trials = Trial.get_trial_group_members(settings=settings, model_filter=model_name)
    
    context['trial_groups'] = Trial.get_all_trial_group_metadata(settings=settings, trial_group_members=trial_group_members)
    context['trial_groups'].sort(key=lambda item: item['time'], reverse=True)

    context['form'] = form

    path = path.rstrip('/')

    codebase_data = CodeBase.get_code_data(
        blob_path='%s/models/%s/%s' % (settings.MANTRA_PROJECT_ROOT, model_name, path),
        path=path)
    context.update(codebase_data)

    return render(request, 'view_codebase.html', context)

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

    context = {}

    yaml_content = Trial.get_trial_group_name_dict(settings=settings)

    try:
        context['trial_group_name'] = yaml_content[model_trials[0]['trial_group_hash']]
    except:
        context['trial_group_name'] = 'Trial Group ' + model_trials[0]['trial_group_hash'][:6]

    context['task_name'] = task_name
    context['task_full_name'] = task_full_name
    context['evaluation_name'] = evaluation_name
    context['trial_group_hash'] = model_trials[0]['trial_group_hash']
    context['trials'] = model_trials
    context['latest_trial'] = datetime.datetime.utcfromtimestamp(int(str(max([trial['timestamp'] for trial in model_trials]))))

    hyperparameter_list = []
    metric_name_list = []

    for trial in context['trials']:
        trial.update({'time': datetime.datetime.utcfromtimestamp(int(str(trial['timestamp'])))})
        try:
            trial['metadata'] = yaml.load(open('%s/trials/%s/trial_metadata.yml' % (settings.MANTRA_PROJECT_ROOT, trial['folder_name']), 'r').read())
        except: # can't load yaml
            trial['metadata'] = {}

        if 'hyperparameters' in trial['metadata']:
            hyperparameter_list = hyperparameter_list + list(trial['metadata']['hyperparameters'].keys())
        
        if 'secondary_metrics' in trial['metadata']:
            metric_name_list = metric_name_list + list(trial['metadata']['secondary_metrics'].keys())

    occur = Counter([hyperparm for hyperparm in hyperparameter_list if hyperparm not in ['epochs', 'image_dim']])
    context['hyperparms'] = [i[0] for i in occur.most_common(5)]
    context['metric_names'] = list(set(metric_name_list))

    for trial in context['trials']:
        if 'hyperparameters' in trial['metadata']:
            hyperparm_list = []
            for hyperparm_no, hyperparm in enumerate(context['hyperparms']):
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
            trial.update({'hyperparm_values': [None]*len(context['hyperparms'])})

        if 'secondary_metrics' in trial['metadata']:
            metric_list = []
            for metric_no, metric in enumerate(context['metric_names']):
                if metric in trial['metadata']['secondary_metrics']:
                    metric_list.append(trial['metadata']['secondary_metrics'][metric])
                else:
                    metric_list.append(None)

            trial.update({'metric_values': metric_list})
        else:
            trial.update({'metric_values': [None]*len(context['metric_names'])})

    context['hyperparms'] = [hyperparm.replace('_', ' ').title() for hyperparm in context['hyperparms']]

    context['trials'].sort(key=lambda item: item['time'], reverse=True)

    context['model'] = {}
    context['data'] = {}
    context['model'].update(Mantra.find_model_metadata(model_trials[0]['model_name']))
    context['data'].update(Mantra.find_dataset_metadata(model_trials[0]['data_name']))
    context['form'] = form 

    return render(request, 'view_trial_group.html', context)

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

    context = {}
    context['scalars'] = scalar_values
    context['latest_media'] = Mantra.find_latest_trial_media(trial_folder_name)

    sys.path.append(settings.MANTRA_PROJECT_ROOT)

    context['model'] = {}
    context['data'] = {}

    context['model'].update(Mantra.find_model_metadata(model_trial['model_name']))
    context['data'].update(Mantra.find_dataset_metadata(model_trial['data_name']))

    return render(request, 'view_trial.html', context)

def view_trial_tensorboard(request, trial_folder):
    """
    This view shows an individual trial with tensorboard
    """

    trials = Trial.get_trial_contents_as_dicts(settings=settings)
    model_trials =  [trial for trial in trials if trial_folder in trial['folder_name']]

    if not model_trials:
        raise Http404("Trial does not exist")
    else:
        model_trial = model_trials[0]
        trial_folder_name = model_trials[0]['folder_name']
    
    subprocess.run(['pkill', '-f', 'tensorboard'], stderr=subprocess.DEVNULL)
    path = '%s/trials/%s/logs' % (settings.MANTRA_PROJECT_ROOT, trial_folder_name)
    subprocess.Popen(['tensorboard', '--logdir', path], stdout=subprocess.DEVNULL)

    time.sleep(2)

    return render(request, 'view_trial_tensorboard.html', {})