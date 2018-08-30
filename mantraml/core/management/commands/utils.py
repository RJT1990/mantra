import os
import shutil
import importlib
from termcolor import colored
import sys

from mantraml.models.TFModel import TFModel
from mantraml.models.KerasModel import KerasModel

from mantraml.data.Dataset import Dataset
from mantraml.data.ImageDataset import ImageDataset
from mantraml.data.TabularDataset import TabularDataset
from mantraml.data.finders import find_dataset_class, find_model_class, find_task_class

from mantraml.core.cloud import AWS
from mantraml import __version__

from .consts import CONFIG_VARIABLES

def adjust_no_tar_data_folder(data_dir):
    """
    This method adjusts a data folder by removing the raw folder and removing the tar name reference in the data.py file.
    We use this method for data projects where there is no tar file and the data is imported some other way, e.g. by API.
    
    Parameters
    -----------
    data_dir - str
        Path of the data directory

    Returns
    -----------
    void - adjusts the data folder
    """

    shutil.rmtree(data_dir + '/raw')

    with open(data_dir + '/data.py','r+') as config:
        contents = config.read() 
        new_contents = contents.replace("files = ['example_dataset.tar.gz']", "files = []")
        config.seek(0) 
        config.write(new_contents)
        config.truncate()
        config.close()

def adjust_tar_data_folder(data_dir, data_name, tar_path):
    """
    This method adjusts a data folder by reading the tar file and changing the metadata in the data.py class to reflect
    what is in the tar folder.
    
    Parameters
    -----------
    data_dir - str
        Path of the data directory

    data_name - str
        Name of the new dataset

    tar_path - str
        Location of the tar file

    Returns
    -----------
    void - adjusts the data folder
    """

    if not tar_path.endswith('.tar.gz'):
        raise ValueError('The tar file does not end with .tar.gz')

    shutil.rmtree(data_dir + '/raw')
    os.mkdir(data_dir + '/raw')
    tar_file_name = tar_path.split('/')[-1]
    shutil.copyfile(tar_path, '%s/%s/%s' % (data_dir, 'raw', tar_file_name))

    with open(data_dir + '/data.py','r+') as config:
        contents = config.read() 
        new_contents = contents.replace("files = ['example_dataset.tar.gz']", "files = ['%s']" % tar_file_name)
        config.seek(0) 
        config.write(new_contents)
        config.truncate()
        config.close()

def adjust_data_folder_for_data_type(args, data_dir):
    """
    This method adjusts a data folder for the data type (e.g. image data or tabular data)
    
    Parameters
    -----------
    args - argument object
        Containing user based options for data 

    data_dir - str
        Path of the data directory

    Returns
    -----------
    void - adjusts the data folder
    """

    if args.template == 'images':

        with open(data_dir + '/data.py','r+') as config:
            new_contents = config.read() 

            if args.image_dim:
                new_contents = new_contents.replace("image_dim = (128, 128)", "image_dim = %s" % str(tuple(args.image_dim)))
            
            if args.normalize:
                new_contents = new_contents.replace("normalized = True", "normalized = %s" % str(args.normalize))
        
            if args.tar_path:
                tar_file_name = args.tar_path.split('/')[-1]
                new_contents = new_contents.replace("image_dataset = 'example_dataset.tar.gz'", "image_dataset = '%s'" % tar_file_name)

            config.seek(0) 
            config.write(new_contents)
            config.truncate()
            config.close()

    elif args.template == 'tabular':

        with open(data_dir + '/data.py','r+') as config:
            new_contents = config.read() 

            if args.file_name:
                new_contents = new_contents.replace("data_file = 'example_dataset.csv'", " data_file = '%s'" % args.file_name)
            
            if args.target:
                new_contents = new_contents.replace("target=None", "target='%s'" % args.target)
            elif args.target_index:
                new_contents = new_contents.replace("target_index=None", "target_index=%s" % args.target)

            if args.features:
                new_contents = new_contents.replace("features=None", "features=%s" % args.features)
            elif args.features_index:
                new_contents = new_contents.replace("features_index=None", "features_index=%s" % args.features_index)

            config.seek(0) 
            config.write(new_contents)
            config.truncate()
            config.close()

def artefacts_create_folder(prog_name, project_dir, args):
    """
    Creates a new artefact folder - data or models - in the project directory

    Parameters
    -----------
    prog_name - str
        The name of the programme - e.g. "makemodel" or "make data"

    project_dir - str
        The directory of the project

    args - NameSpace
        Arguments specified by the user from the Mantra command line

    Returns
    -----------
    void - creates a new artefact folder
    """

    # Find the type of folder request
    if prog_name == 'makemodel':
        template_folder = 'models'
    elif prog_name == 'makedata':
        template_folder = 'data'
    elif prog_name == 'maketask':
        template_folder = 'tasks'
    else:
        return

    # Process the template
    if args.template:
        template_name = args.template
    else:
        template_name = 'default'

    # some configuration details
    library_path = '/'.join(os.path.realpath(__file__).split('/')[:-4])

    default_template_path = '%s/templates/%s/%s' % (library_path, template_folder, template_name)

    if template_folder == 'models':

        default_template_path = '%s/templates/%s/%s/base' % (library_path, template_folder, template_name)

        if args.framework:
            if args.framework in ['tensorflow', 'keras', 'pytorch']:
                default_template_path = '%s/templates/%s/%s/%s' % (library_path, template_folder, args.framework, template_name)
            else:
                raise ValueError('The framework name you entered - %s - was not recognised' % args.framework)

    component_dir = '%s/%s/%s' % (project_dir, template_folder, args.path)

    # copy the template folder to the user's project
    try:
        shutil.copytree(default_template_path, component_dir, ignore=shutil.ignore_patterns('*.pyc', '__pycache__*'))
    except FileExistsError:
        raise Exception("'%s' folder exists already" % component_dir)
    except OSError as e:
        raise Exception(e)

    if template_folder == 'data':
        if args.no_tar: # if the user has specified no tar file
            adjust_no_tar_data_folder(data_dir=component_dir)
            return

        if args.tar_path: # if the user wants a tar file copied to the new project directory
            adjust_tar_data_folder(data_dir=component_dir, data_name=args.path, tar_path=args.tar_path)

        adjust_data_folder_for_data_type(args=args, data_dir=component_dir)

def train_model(project_name, settings, args, **kwargs):
    """
    Trains a model - either cloud or locally - with the user's requested parameters

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

    Returns
    ---------
    void - trains a machine learning model either locally or via the cloud
    """

    if args.cloud:

        if any([not hasattr(settings, config_var) for config_var in CONFIG_VARIABLES]):
            raise AttributeError(colored('You have not set up your cloud configuration yet. To do this run:\n', 'red') + colored(' mantra cloud', 'blue'))

        if settings.CLOUD_PROVIDER == 'AWS':

            # get dataset
            sys.path.append(os.getcwd())
            data_module = importlib.import_module("data.%s.data" % args.dataset)
            dataset_class = find_dataset_class(data_module)

            # cloud setup
            cloud_instance = AWS(
                settings=settings,
                instance_ids=args.instance_ids,
                project_name=project_name,
                dataset_class=dataset_class,
                dev=args.dev)
            cloud_instance.setup(args=args, **kwargs)
            cloud_instance.train(args=args)

    else:
        # Import data
        sys.path.append(os.getcwd())
        data_module = importlib.import_module("data.%s.data" % args.dataset)
        dataset_class = find_dataset_class(data_module)
        if dataset_class:
            dataset = dataset_class(name=args.dataset, trial=True, **kwargs)

            model_module = importlib.import_module("models.%s.model" % args.model_name)
            model_class = find_model_class(model_module)
                
            task_class = None

            if args.task:
                task_module = importlib.import_module("tasks.%s.task" % args.task)
                task_class = find_task_class(task_module)

            if task_class is None:
                task = None
            else:
                task = task_class(data=dataset)

            if model_class:
                model = model_class(args=args, 
                    dataset=dataset, 
                    settings=settings, trial=True, **kwargs)
                model.task = task
                model.run()