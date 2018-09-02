from .Dataset import Dataset
from .ImageDataset import ImageDataset
from .TabularDataset import TabularDataset

from mantraml.models import MantraModel
from mantraml.tasks.Task import Task

# Bade model and data for training
BASE_MODEL_CLASSES = ['MantraModel']
BASE_DATA_CLASSES = ['Dataset', 'TabularDataset', 'ImageDataset']
BASE_TASK_CLASSES = ['Task']

def find_dataset_class(data_module):
    """
    Find a dataset class. Returns the first dataset class it finds -  Dataset object should be a singleton within a data project

    Parameters
    -----------
    data_module - module
        Module that potentially contains mantraml.Dataset type objects

    Returns
    ------------
    mantraml.Dataset object - any Dataset objects found within the modle
    """

    dataset = None

    for obj_key, obj_value in data_module.__dict__.items():

        if obj_key in BASE_DATA_CLASSES:
            continue
        elif hasattr(data_module.__dict__[obj_key], '__bases__'):
            if data_module.__dict__[obj_key].__bases__[0] in [Dataset, TabularDataset, ImageDataset]:
                dataset = data_module.__dict__[obj_key]
                break

    return dataset


def find_model_class(model_module):
    """
    Find a model class. Returns the first model class it finds -  Model object should be a singleton within a data project

    Parameters
    -----------
    model_module - module
        Module that potentially contains mantraml.BaseModel type objects

    Returns
    ------------
    mantraml.BaseModel type object - any BaseModel type objects found within the modle
    """

    model = None

    for obj_key, obj_value in model_module.__dict__.items():

        if obj_key in BASE_MODEL_CLASSES:
            continue
        elif hasattr(model_module.__dict__[obj_key], '__bases__'):
            if model_module.__dict__[obj_key].__bases__[0] in [MantraModel]:
                model = model_module.__dict__[obj_key]

    return model


def find_task_class(task_module):
    """
    Find a task class. Returns the first task class it finds -  task object should be a singleton within a task project

    Parameters
    -----------
    tasl_module - module
        Module that potentially contains mantraml.Task type objects

    Returns
    ------------
    mantraml.Task object - any Task objects found within the module
    """

    task = None

    for obj_key, obj_value in task_module.__dict__.items():

        if obj_key in BASE_TASK_CLASSES:
            continue
        elif hasattr(task_module.__dict__[obj_key], '__bases__'):
            if task_module.__dict__[obj_key].__bases__[0] in [Task]:
                task = task_module.__dict__[obj_key]
                break

    return task

def find_framework(model_module):
    """
    Find the deep learning framework used from a module - based on items on the module

    Parameters
    -----------
    model_module - module
        Module that contains the core model logic

    Returns
    ------------
    str - with the framework name
    """

    tensorflow_imports = len([module for module in dir(model_module) if 'tensorflow' in module or 'tf' in module])
    torch_imports = len([module for module in dir(model_module) if 'torch' in module])

    if tensorflow_imports or torch_imports:
        if tensorflow_imports > torch_imports:
            return 'tensorflow'
        elif torch_imports > tensorflow_imports:
            return 'pytorch'
        else:
            return 'tensorflow'
    else:
        return 'none'