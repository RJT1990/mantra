import datetime
import glob
import importlib
import inspect
import itertools
import json
import matplotlib.pyplot as plt
import os
import pandas as pd
from pandas.plotting import table
import PIL
import shutil
import subprocess
import sys
import tarfile

from django.conf import settings
import lazy_import
yaml = lazy_import.lazy_module("yaml")

from mantraml.data.finders import find_dataset_class, find_model_class, find_task_class, find_framework
from mantraml.data.Dataset import Dataset
from mantraml.data.ImageDataset import ImageDataset
from mantraml.data.TabularDataset import TabularDataset
from mantraml.models.TFModel import TFModel
from mantraml.models.KerasModel import KerasModel


from .consts import IGNORED_FILES, NO_OF_ARTEFACTS


class Mantra:
    config = None

    @classmethod
    def get_config(cls):
        """
        Load in the mantra.yml config file, always use this and don't access the
        class attribute directly.

        :return:
        """
        if cls.config is None:
            config_file = os.path.join(settings.MANTRA_PROJECT_ROOT, "mantra.yml")

            if not os.path.isfile(config_file):
                print("ERROR: Missing 'mantra.yml' config file at '%s'" % settings.MANTRA_PROJECT_ROOT)
            cls.config = yaml.load(open(config_file))

        return cls.config

    @staticmethod
    def find_latest_trial_media(trial_folder):
        """
        For a trial folder, finds the latest trial media (e.g. images)
        """

        media_files = []

        for ext in ['png', 'jpg', 'jpeg']:
            media_files = media_files + glob.glob('%s/trials/%s/media/*%s' % (settings.MANTRA_PROJECT_ROOT, trial_folder, ext))

        try:
            return max(media_files, key=os.path.getctime).split(settings.MANTRA_PROJECT_ROOT + '/')[1]
        except IndexError:
            return None
        except ValueError:
            return None

    @staticmethod
    def find_model_metadata(model_name):
        """
        Finds the model metadata 
        """
        metadata = {}

        model_module = importlib.import_module("models.%s.model" % model_name)
        model_class = find_model_class(model_module)
        model_framework = find_framework(model_module)

        if model_framework == 'tensorflow':
            metadata['framework'] = 'tf'
        elif model_framework == 'pytorch':
            metadata['framework'] = 'pytorch'
        else:
            metadata['framework'] = 'none'

        if hasattr(model_class, 'model_name'):
            metadata['name'] = model_class.model_name
        else:
            metadata['name'] = model_name

        if hasattr(model_class, 'model_arxiv_id'):
            metadata['arxiv_pdf'] = 'https://arxiv.org/pdf/%s.pdf' % model_class.model_arxiv_id
        else:
            metadata['arxiv_pdf'] = None

        if hasattr(model_class, 'model_pdf'):
            metadata['pdf'] = model_class.model_pdf
        else:
            metadata['pdf'] = None

        if hasattr(model_class, 'model_tags'):
            metadata['tags'] = model_class.model_tags
        else:
            metadata['tags'] = []

        if hasattr(model_class, 'model_notebook'):
            notebook_path = '%s/models/%s/%s' % (settings.MANTRA_PROJECT_ROOT, model_name, model_class.model_notebook)
            output = subprocess.Popen(["cat", notebook_path], stdout=subprocess.PIPE).stdout.read().decode('utf-8')
            output = json.dumps(output)
            metadata['notebook'] = output
        else:
            metadata['notebook'] = None

        if hasattr(model_class, 'model_image'):
            metadata['image'] = 'models/%s/%s' % (model_name, model_class.model_image)
        else:
            metadata['image'] = 'img/default_model.jpg'

        metadata['folder_name'] = model_name

        return metadata

    @staticmethod
    def extract_data_files(dataset_name, dataset_class, data_location, sample_location, extract_loc, n=16):
        """
        Extracts a sample of data files to use for a dataset preview image/soundbite/etc

        n : number of samples (16 is default for a 4x4 image grid)
        """

        tar_location = '%sraw' % data_location

        for file in sorted(dataset_class.files):

            file_path = '%sraw/%s' % (data_location, file)

            if 'tar.gz' in file:
                tar = tarfile.open(file_path, mode='r')

                files_at_top = False

                members = tar.getmembers()

                for member in members:
                    if '/' not in member.name and member.isfile():
                        files_at_top = True
                        break

                if os.path.isdir(data_location + 'raw/extract'):
                    shutil.rmtree(data_location + 'raw/extract')

                if n is None:
                    members = members
                else:
                    members = members[:n]

                if files_at_top:
                    tar.extractall(members=members, path=extract_loc)
                else:
                    top_level_dir = os.path.commonprefix(tar.getnames())
                    tar.extractall(members=members, path='%s%s' % (data_location, 'raw'))
                    os.rename('%sraw/%s' % (data_location, top_level_dir), extract_loc)

                images = ['%s/%s' % (extract_loc, image) for image in os.listdir(extract_loc)]

            shutil.copy(file_path, extract_loc)

        return images

    @classmethod
    def generate_image_sample(cls, dataset_name, dataset_class, data_location, sample_location):
        """
        Generates a jpg from a sample of the image dataset
        """

        extract_loc = '%sraw/%s' % (data_location, 'sample_extract')

        extracted_files = cls.extract_data_files(dataset_name, dataset_class, data_location, sample_location, extract_loc)

        size_figure_grid = 4
        fig, ax = plt.subplots(size_figure_grid, size_figure_grid)
        for i, j in itertools.product(range(size_figure_grid), range(size_figure_grid)):
            ax[i, j].get_xaxis().set_visible(False)
            ax[i, j].get_yaxis().set_visible(False)

        for k in range(size_figure_grid*size_figure_grid):
            i = k // size_figure_grid
            j = k % size_figure_grid
            ax[i, j].cla()
            ax[i, j].axis('off')

            try:
                img = PIL.Image.open(extracted_files[k])
                ax[i, j].imshow(img)
            except IndexError:
                continue # if no image exists, plot nothing in that grid
            except OSError:
                continue # if image can't be processed, plot nothing in that grid

        plt.subplots_adjust(wspace=0, hspace=0)
        plt.savefig(sample_location)

        shutil.rmtree(extract_loc)

    @classmethod
    def generate_tabular_sample(cls, dataset_name, dataset_class, data_location, sample_location):
        """
        Generates a jpg from a sample of the pandas DataFrame
        """

        extract_loc = '%sraw/%s' % (data_location, 'sample_extract')
        file_to_extract = inspect.signature(dataset_class.__init__).parameters['file_name'].default
        _ = cls.extract_data_files(dataset_name, dataset_class, data_location, sample_location, extract_loc, None)

        # define the core DataFrames
        file_type = file_to_extract.split('.')[-1] 
        if file_type == 'csv':
            df = pd.read_csv('%s/%s' % ('%s%s' % (data_location, 'raw/sample_extract'), file_to_extract)).head()
        else:
            df = pd.DataFrame()

        plt.figure()

        cell_text = []
        for row in range(len(df)):
            cell_text.append(df.iloc[row, :3])

        plt.table(cellText=cell_text, colLabels=df.columns[:3], loc='center')
        plt.axis('off')

        plt.savefig(sample_location)

        shutil.rmtree(extract_loc)

    @classmethod
    def find_image_dataset_sample(cls, dataset_name, dataset_class):
        """
        Finds/creates an image that has a sample of the data
        """
        data_location = '%s/data/%s/' % (settings.MANTRA_PROJECT_ROOT, dataset_name)

        sample_location = '%sraw/sample.jpg' % data_location
        png_sample_location = '%sraw/sample.png' % data_location

        if not os.path.exists(sample_location):

            if os.path.exists(png_sample_location):
                return 'data/%s/raw/sample.png' % dataset_name

            cls.generate_image_sample(dataset_name, dataset_class, data_location, sample_location)

        return 'data/%s/raw/sample.jpg' % dataset_name

    @classmethod
    def find_tabular_dataset_sample(cls, dataset_name, dataset_class):
        """
        Finds/creates an image that has a sample of the data
        """
        data_location = '%s/data/%s/' % (settings.MANTRA_PROJECT_ROOT, dataset_name)

        sample_location = '%sraw/sample.jpg' % data_location

        if not os.path.exists(sample_location):
            cls.generate_tabular_sample(dataset_name, dataset_class, data_location, sample_location)

        return 'data/%s/raw/sample.jpg' % dataset_name

    @classmethod
    def find_dataset_metadata(cls, dataset_name):
        """
        Finds the dataset metadata 
        """
        metadata = {}

        dataset_module = importlib.import_module("data.%s.data" % dataset_name)
        dataset_class = find_dataset_class(dataset_module)

        if hasattr(dataset_class, 'dataset_type'):
            metadata['dataset_image'] = 'img/default_model.jpg'

            if dataset_class.dataset_type == 'images':
                metadata['dataset_type'] = 'images'
                metadata['dataset_image'] = cls.find_image_dataset_sample(dataset_name, dataset_class)
            elif dataset_class.dataset_type == 'music':
                metadata['dataset_type'] = 'music'
            elif dataset_class.dataset_type == 'tabular':
                metadata['dataset_type'] = 'tabular'
                metadata['dataset_image'] = cls.find_tabular_dataset_sample(dataset_name, dataset_class)
            else:
                metadata['dataset_type'] = 'base'

        else:
            metadata['dataset_type'] = 'base'
            metadata['dataset_image'] = 'img/default_model.jpg'

        if hasattr(dataset_class, 'dataset_name'):
            metadata['name'] = dataset_class.dataset_name
        else:
            metadata['name'] = dataset_name

        if hasattr(dataset_class, 'dataset_tags'):
            metadata['tags'] = dataset_class.dataset_tags
        else:
            metadata['tags'] = []

        if hasattr(dataset_class, 'dataset_notebook'):
            notebook_path = '%s/data/%s/%s' % (settings.MANTRA_PROJECT_ROOT, dataset_name, dataset_class.dataset_notebook)
            output = subprocess.Popen(["cat", notebook_path], stdout=subprocess.PIPE).stdout.read().decode('utf-8')
            output = json.dumps(output)
            metadata['notebook'] = output
        else:
            metadata['notebook'] = None

        metadata['folder_name'] = dataset_name

        return metadata

    @classmethod
    def find_task_metadata(cls, task_name):
        """
        Finds the task metadata 
        """

        if task_name == 'none':
            return {'name': None}

        metadata = {}

        task_module = importlib.import_module("tasks.%s.task" % task_name)
        task_class = find_task_class(task_module)

        if hasattr(task_class, 'task_name'):
            metadata['name'] = task_class.task_name
        else:
            metadata['name'] = task_name

        if hasattr(task_class, 'evaluation_name'):
            metadata['evaluation_name'] = task_class.evaluation_name
        else:
            metadata['evaluation_name'] = 'Unknown'

        metadata['folder_name'] = task_name

        return metadata

    @staticmethod
    def remove_ignored_files(blobs):
        """
        Removes ignored files/folders from the retrieval
        """

        return [blob for blob in blobs if blob not in IGNORED_FILES]

    @staticmethod
    def format_timestamp_data(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%d %B %Y %I:%M %p').lstrip("0").replace(" 0", " ")

    @classmethod
    def get_models(cls, limit=True):
        """
        List the models associated with the current Mantra project (gets the most recent)

        :return:
        """
        config = cls.get_config()

        models_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["models_folder"])
        if os.path.isdir(models_dir):
            models_list = [o for o in os.listdir(models_dir) if os.path.isdir(os.path.join(models_dir, o))]
        else:
            models_list = []

        models_list = cls.remove_ignored_files(models_list)
        model_time_dict = {model_name: os.path.getmtime('%s/%s' % (models_dir, model_name)) for model_name in models_list}

        if limit:
            latest_models =  sorted(model_time_dict, key=model_time_dict.get, reverse=True)[:NO_OF_ARTEFACTS]
        else:
            latest_models =  sorted(model_time_dict, key=model_time_dict.get, reverse=True)

        sys.path.append(settings.MANTRA_PROJECT_ROOT)

        return [{
        'last_updated': cls.format_timestamp_data(model_time_dict[model_name]), **cls.find_model_metadata(model_name)} for model_name in latest_models]

    @classmethod
    def get_datasets(cls, limit=True):
        """
        List the datasets associated with the current Mantra project

        :return:
        """
        config = cls.get_config()

        data_dir = os.path.join(settings.MANTRA_PROJECT_ROOT, config["data_folder"])
        if os.path.isdir(data_dir):
            data_list = [o for o in os.listdir(data_dir) if os.path.isdir(os.path.join(data_dir, o))]
        else:
            data_list = []

        datasets_list = cls.remove_ignored_files(data_list)
        dataset_time_dict = {dataset_name: os.path.getmtime('%s/%s' % (data_dir, dataset_name)) for dataset_name in datasets_list}
        
        if limit:
            latest_datasets = sorted(dataset_time_dict, key=dataset_time_dict.get, reverse=True)[:NO_OF_ARTEFACTS]
        else:
            latest_datasets = sorted(dataset_time_dict, key=dataset_time_dict.get, reverse=True)

        return [{
        'last_updated': cls.format_timestamp_data(dataset_time_dict[dataset_name]), **cls.find_dataset_metadata(dataset_name)} for dataset_name in latest_datasets]