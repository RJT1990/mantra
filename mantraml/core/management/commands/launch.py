import os
import shutil
import uuid

from mantraml.core.management.commands.BaseCommand import BaseCommand
from mantraml import __version__


class LaunchCmd(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('project_name', type=str, help='Name of the Mantra project')
        return parser

    @staticmethod
    def write_new_content(file_path, text):
        """
        This function takes a file and some text, and writes the file to text

        Parameters
        -----------
        file_path - str
            The path of the file

        text - str
            The text to write to the file


        Returns
        -----------
        void - updates the file
        """

        with open(file_path, 'r+') as file:
            file.read()
            file.seek(0)
            file.write(text)
            file.truncate()
            file.close()

    @staticmethod
    def replace_content(file_path, old_text, new_text):
        """
        This function takes a file and replaces some old_text with new_text

        Parameters
        -----------
        file_path - str
            The path of the file

        old_text - str
            The text within the file that we want to replace

        new_text - str
            The text we want to put in the place of the old_text

        Returns
        -----------
        void - updates the file
        """

        with open(file_path, 'r+') as file:
            contents = file.read()
            new_contents = contents.replace(old_text, new_text)
            file.seek(0)
            file.write(new_contents)
            file.truncate()
            file.close()

    def configure_project(self, project_name, top_dir):
        """
        This method configures a new project

        Parameters
        -----------
        
        project_name - str
            Name of the project

        top_dir - str
            The directory of the project

        Returns
        -----------
        void - updates the files in the project
        """

        readme_text =  "# %s\n\nYour first Mantra project - huzzah!" % project_name

        self.write_new_content(file_path=top_dir + '/README.md', text=readme_text)
        self.write_new_content(file_path=top_dir + '/requirements.txt', text='mantraml==%s' % __version__)
        self.replace_content(file_path=top_dir + '/mantra.yml', old_text='default_name', new_text=project_name)
        self.replace_content(file_path=top_dir + '/settings.py', old_text='default-s3-bucket-name', new_text='%s-%s' % (project_name.lower().replace('_', '-'), str(uuid.uuid4())))

    def handle(self, args, unknown):
        """
        Creates a new project directory based on the name and template given by the user; configures the project
        """

        project_name = args.project_name

        library_path = '/'.join(os.path.realpath(__file__).split('/')[:-4])
        default_template_path = '%s/templates/projects/default' % library_path

        top_dir = os.path.join(os.getcwd(), project_name)
        
        # copy the project template to the path the user specified
        try:
            shutil.copytree(default_template_path, top_dir, ignore=shutil.ignore_patterns('*.pyc', '__pycache__*'))
        except FileExistsError:
            raise Exception("'%s' folder exists already" % top_dir)
        except OSError as e:
            raise Exception(e)

        self.configure_project(project_name, top_dir)