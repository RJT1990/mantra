import datetime
import json
import os
import subprocess
import sys


class CodeBase:


    @staticmethod
    def format_timestamp_data(timestamp):
        return datetime.datetime.fromtimestamp(timestamp).strftime('%d %B %Y %I:%M %p').lstrip("0").replace(" 0", " ")

    @classmethod
    def get_code_data(cls, blob_path, path):
        """
        This method gets information on the files, directories and more from a path given

        Parameters
        -----------
        blob_path - str
            The full path where the code is located, including project name and data folder

        path - str
            The local path where the code is located

        Returns
        -----------
        dict - contains information on the files, directories and more in the path
        """

        codebase_data = {}

        codebase_data['file_contents'], codebase_data['is_folder'], codebase_data['file_type'] = cls.show_file(blob_path)
        codebase_data['file_lines'] = len(codebase_data['file_contents'].split('\n'))
        codebase_data['file_size'] = sys.getsizeof(codebase_data['file_contents'])

        # Project readme
        codebase_data['directories'], codebase_data['files'] = None, None

        if codebase_data['is_folder']:
            codebase_data['directories'] = cls.get_directories(blob_path)
            codebase_data['files'] = cls.get_files(blob_path)
            codebase_data['file_extension'] = ''
        else:
            codebase_data['file_extension'] = path.split('.')[-1]

        codebase_data['path_list'] = CodeBase.get_path_list('/%s' % path)
        codebase_data['path'] = path

        return codebase_data

    @classmethod
    def get_directories(cls, cwd):
        """
        Gets a list of directories from a chosen working directory

        Parameters
        -----------
        cwd - str
            The working directory to run the command from

        Returns
        -----------
        list - list of strs (directory names)
        """

        dirs = subprocess.run('ls -d */', shell=True, stdout=subprocess.PIPE, cwd=cwd).stdout.decode('utf-8').split('\n')
        dirs = sorted([dir.replace('/', '') for dir in dirs if dir not in ['', '__pycache__/']], key=str.lower)

        directories = [{'name': dir_name, 'last_modified': cls.format_timestamp_data(os.path.getmtime('%s/%s' % (cwd, dir_name)))} for dir_name in dirs]

        return directories

    @classmethod
    def get_file_icon(cls, file_name):
        """
        Gets an ionicon logo based on the file extension
        """

        if '.py' in file_name:
            return 'logo-python'
        if any([img in file_name for img in ['.png', '.jpg', '.jpeg']]):
            return 'image'
        else:
            return 'document'

    @classmethod
    def get_files(cls, cwd):
        """
        Gets a list of directories from a chosen working directory

        Parameters
        -----------
        cwd - str
            The working directory to run the command from

        Returns
        -----------
        list - list of strs (directory names)
        """

        files = subprocess.run('ls -p | grep -v /', shell=True, stdout=subprocess.PIPE, cwd=cwd).stdout.decode('utf-8').split('\n')
        files = sorted([file for file in files if file], key=str.lower)

        files = [{'name': file_name, 
        'last_modified': cls.format_timestamp_data(os.path.getmtime('%s/%s' % (cwd, file_name))),
        'icon': cls.get_file_icon(file_name)} for file_name in files]
        
        return files

    @staticmethod
    def get_path_list(path):
        """
        This method creates a list of path elements

        Parameters
        ----------
        path - str
            Path of the repository

        Returns
        ----------
        list - list of lists (each list contains the item in the path, whether it is the end of the path (final file), 
        and its full directory)
        """

        path_list = []
        if '/' not in path:
            return path_list

        path_elements = path.split('/')

        for path_no, path_item in enumerate(path_elements):
            if path_no == len(path_elements) - 1:
                end_of_tree = True
            else:
                end_of_tree = False

            path_list.append([path_item, end_of_tree, '/'.join(path_elements[:path_no+1]).lstrip('/')])

        return path_list

    @classmethod
    def get_readme(cls, path):
        """
        Get the README from the path

        Parameters
        -----------
        path - str
            The location of the file or folder

        Returns
        -----------
        str - the contents of a file, bool - whether the README exists
        """

        if not os.path.isfile(path + '/README.md'):
            return '', False

        output = subprocess.Popen(["cat", path + '/README.md'], stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        
        return output, True

    @classmethod
    def show_file(cls, path):
        """
        Shows the contents of a file, along with a boolean of whether it is a file or a directory

        Parameters
        -----------
        path - str
            The location of the file or folder

        Returns
        -----------
        str - the contents of a file, bool - whether it's a folder or not, str - file type
        """

        if not os.path.isfile(path):
            return '', True, 'folder'

        is_folder = False

        if any([img_type in path for img_type in ['.png', 'jpg', '.jpeg']]):
            return '', False, 'image'
        elif '.md' in path:
            import pdb
            pdb.set_trace()

            output = subprocess.Popen(["cat", path], stdout=subprocess.PIPE).stdout.read().decode('utf-8')
            return output, False, 'markdown'
        elif '.ipynb' in path:
            output = subprocess.Popen(["cat", path], stdout=subprocess.PIPE).stdout.read().decode('utf-8')
            output = json.dumps(output)
            return output, False, 'notebook'
        else:
            output = subprocess.Popen(["cat", path], stdout=subprocess.PIPE).stdout.read().decode('utf-8')
            return output, False, 'other'