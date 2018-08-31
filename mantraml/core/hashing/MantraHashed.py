import binascii
import datetime
import hashlib
import os
import shutil
import stat
import zlib

BUF_SIZE = 65536  # read files in 64kb chunks


class MantraHashed(object):
    """
    Contains methods for hashing files, storing hashed files, and general model/data version control
    """

    @staticmethod
    def get_256_hash_from_file(file_location):
        """
        This method calculates the SHA256 hash of a file

        Parameters
        -----------
        file_location - str
            The location of the file to be hashed

        Returns
        -----------
        str - the SHA256 hash of the file
        """

        sha256 = hashlib.sha256()

        with open(file_location, 'rb') as f:
            while True:
                data = f.read(BUF_SIZE)
                if not data:
                    break
                sha256.update(data)

        return sha256.hexdigest()

    @staticmethod
    def get_256_hash_from_string(string):
        """
        This method calculates the SHA256 hash of a string

        Parameters
        -----------
        string - str
            The string to be hashed

        Returns
        -----------
        str - the SHA256 hash of the string
        """

        sha256 = hashlib.sha256()
        sha256.update(string.encode('utf-8'))

        return sha256.hexdigest()

    @classmethod
    def create_file_hash_dict(cls, file, file_path):
        """
        This method hashes a file and stores it and other informations such as the file name, permissions etc in a dictionary

        Parameters
        -----------
        file - str
            The name of the file

        file_path - str
            The path of the file

        Returns
        -----------
        dict - containing the hash and other file information
        """

        file_info = {}
        file_info['path'] = file_path
        file_info['hash'] = cls.get_256_hash_from_file(file_path)
        file_info['type'] = 'file'
        file_info['name'] = file
        file_info['perm'] = stat.S_IMODE(os.lstat(file_path).st_mode)

        return file_info

    @classmethod
    def get_tree_contents(cls, tree_path, dirs, files, ref_table):
        """
        This method gets a hash for a tree

        Parameters
        -----------
        tree_path - str
            The path of the tree

        dirs - list
            List of directories within the tree

        files - list
            List of files within the tree

        ref_table - dict
            Current dictionary of file and tree hash information; keys are paths; values are dicts containing keys on hashs, file permissions, etc

        Returns
        -----------
        str containing the tree contents, hash of the contents
        """

        tree_contents = ''

        for dir_name in dirs:
            dir_name_path = '%s/%s' % (tree_path, dir_name)
            dir_name_perm = ref_table[dir_name_path]['perm']
            tree_contents += '%s tree %s %s \n' % (dir_name_perm, ref_table[dir_name_path]['hash'], dir_name)

        for file in files:
            file_path = '%s/%s' % (tree_path, file)
            file_perm = ref_table[file_path]['perm']
            tree_contents += '%s file %s %s \n' % (file_perm, ref_table[file_path]['hash'], file)

        return tree_contents, cls.get_256_hash_from_string(tree_contents)

    @classmethod
    def create_tree_hash_dict(cls, current_dir, file_path, dirs, files, ref_table):
        """
        This method hashes a tree and stores it and other informations such as the file name, permissions etc in a dictionary

        Parameters
        -----------
        current_dir - str
            Current directory name (str)

        file_path - str
            The path of the tree

        dirs - list
            List of directories within the tree

        files - list
            List of files within the tree

        ref_table - dict
            Current dictionary of file and tree hash information; keys are paths; values are dicts containing keys on hashs, file permissions, etc

        Returns
        -----------
        dict - containing the hash and other tree information
        """

        # we sort just to ensure there are no arrangement issues that could affect the hash outcome
        file_hashs = sorted([ref_table['%s/%s' % (file_path, file)]['hash'] for file in files])
        dir_hashs = sorted([ref_table['%s/%s' % (file_path, dir_name)]['hash'] for dir_name in dirs])

        tree_info = {}
        tree_info['path'] = file_path
        tree_info['content'], tree_info['hash'] = cls.get_tree_contents(file_path, dirs, files, ref_table)
        tree_info['type'] = 'tree'
        tree_info['name'] = current_dir
        tree_info['perm'] = stat.S_IMODE(os.lstat(file_path).st_mode)

        return tree_info

    @classmethod
    def get_data_dependency_hash(cls, data_dir, dataset_class):
        """
        This method takes a dataset_class, with a files class variable, and works out the concatenated hash
        from the files. We use this to get an hash of the dataset dependencies, so we can compare hashes
        of these dependencies between environments (local and cloud) and know whether to transfer large
        files or not (if they have changed).

        Parameters
        -----------
        data_dir - str
            The directory of the data folder

        dataset_class - mantraml.Dataset type class
            Containing a files class variable that we will calculate a concatenated hash for

        Returns
        ---------
        str - SHA-256 hash of the data dependencies
        """

        file_hashes = []

        for file in sorted(dataset_class.files):

            if not os.path.isfile('%sraw/%s' % (data_dir, file)):
                raise IOError('The following file that was referenced in your Dataset class does not exist: %s' % file)

            tar_hash = MantraHashed.get_256_hash_from_file('%sraw/%s' % (data_dir, file))
            file_hashes.append(tar_hash)

        return MantraHashed.get_256_hash_from_string(''.join(file_hashes))

    @classmethod
    def get_folder_hash(cls, folder_dir):
        """
        Gets the hash of a model/data folder. Uses a Git style Merkel tree

        Parameters
        -----------
        folder_dir - str
            The directory of the model/data folder

        Returns
        ---------
        str - SHA-256 hash of the model/data folder, hash_dict - dict containing hashes of the files and trees
        """

        hash_dict = {}

        for path, dirs, files in os.walk(folder_dir, topdown=False):

            current_dir = path.split('/')[-1]

            # extracted folders are never stored
            if '.extract/' in path or current_dir == '.extract':
                continue

            for file in files:
                if file == 'hash':
                    continue
                file_path = '%s/%s' % (path, file)
                hash_dict[file_path] = cls.create_file_hash_dict(file, file_path)

            filtered_dirs = [directory for directory in dirs if directory != '.extract']
            hash_dict[path] = cls.create_tree_hash_dict(current_dir, path, filtered_dirs, files, hash_dict)

        return hash_dict[folder_dir]['hash'], hash_dict

    @classmethod
    def save_artefact(cls, cwd, hash, objects, args, artefact_type='MODELS', **kwargs):
        """
        Saves the model/data objects to a hidden folder - in case the user wants to revert to that model/data at any point

        Parameters
        -----------
        cwd - str
            Current working directory

        hash - str
            The hash of the model/data folder

        objects - dict
            keys with file/tree paths, and values containing hash information

        args - NameSpace
            Additional arguments that the user entered through the training

        artefact_type - str
            Either MODELS or DATA (depending on the artefact)

        Returns
        ---------
        bool - whether model/data is new or not
        """

        objects_dir = '%s/%s' % (cwd, '.mantra/objects')

        if os.path.isfile('%s/%s/%s' % (objects_dir, hash[:2], hash[2:])):
            return False # hash already exists, we have already stored the object

        for item_key, item_value in objects.items():
            
            item_loc = '%s/%s/%s' % (objects_dir, item_value['hash'][:2], item_value['hash'][2:])

            if os.path.isfile(item_loc):
                continue

            hash_path = '%s/%s' % (objects_dir, item_value['hash'][:2])

            if not os.path.exists(hash_path):
                os.mkdir(hash_path)

            if item_value['type'] == 'tree':
                f = open(item_loc, "wb")
                f.write(zlib.compress(bytes(item_value['content'].encode('ascii'))))
                f.close()
            else:
                content = zlib.compress(open(item_key, "rb").read())
                f = open(item_loc, "wb")
                f.write(content)
                f.close()

        unix_ts = int((datetime.datetime.utcnow() - datetime.datetime(1970, 1, 1)).total_seconds())
        f = open('%s/%s' % (cwd, '.mantra/%s' % artefact_type), "a")

        if artefact_type == 'MODELS':
            f.write('%s %s %s %s\n' % (hash, unix_ts, args.model_name, 'trained on %s' % args.dataset))
        elif artefact_type == 'DATA':
            f.write('%s %s %s %s\n' % (hash, unix_ts, args.dataset, 'used with model %s' % args.model_name))
        elif artefact_type == 'TASKS':
            f.write('%s %s %s %s\n' % (hash, unix_ts, args.task, 'used with model %s trained on %s' % (args.model_name, args.dataset)))
        f.close()

        return True