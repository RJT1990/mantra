from mantraml.core.hashing.MantraHashed import MantraHashed

def test_get_256_hash_from_string():
    string_to_hash = 'E pluribus unum'
    file_hash = MantraHashed.get_256_hash_from_string(string_to_hash)
    assert(isinstance(file_hash, str))
    assert(len(file_hash) == 64)

def test_create_file_hash_dict():
    file_info = MantraHashed.create_file_hash_dict(__file__, __file__)
    assert(isinstance(file_info, dict))
    assert(file_info['path'] == __file__)
    assert(file_info['hash'] == MantraHashed.get_256_hash_from_file(__file__))
    assert(file_info['type'] == 'file')
    assert(file_info['name'] == __file__)
    assert(isinstance(file_info['perm'], int))    
    assert(len(str(file_info['perm'])) == 3)

def test_get_tree_contents():

    tree_path = '/home/ubuntu'
    dirs = ['folder1', 'folder2']
    files = ['file1', 'file2', 'file3']
    ref_table = {}
    ref_table[tree_path] = {}
    ref_table['%s/%s' % (tree_path, 'folder1')] = {}
    ref_table['%s/%s' % (tree_path, 'folder1')]['perm'] = 700
    ref_table['%s/%s' % (tree_path, 'folder1')]['hash'] = 'hash1'
    ref_table['%s/%s' % (tree_path, 'folder2')] = {}
    ref_table['%s/%s' % (tree_path, 'folder2')]['perm'] = 700
    ref_table['%s/%s' % (tree_path, 'folder2')]['hash'] = 'hash2'
    ref_table['%s/%s' % (tree_path, 'folder3')] = {}
    ref_table['%s/%s' % (tree_path, 'folder3')]['perm'] = 700
    ref_table['%s/%s' % (tree_path, 'folder3')]['hash'] = 'hash3'
    ref_table['%s/%s' % (tree_path, 'file1')] = {}
    ref_table['%s/%s' % (tree_path, 'file1')]['perm'] = 700
    ref_table['%s/%s' % (tree_path, 'file1')]['hash'] = 'hash4'
    ref_table['%s/%s' % (tree_path, 'file2')] = {}
    ref_table['%s/%s' % (tree_path, 'file2')]['perm'] = 700
    ref_table['%s/%s' % (tree_path, 'file2')]['hash'] = 'hash5'
    ref_table['%s/%s' % (tree_path, 'file3')] = {}
    ref_table['%s/%s' % (tree_path, 'file3')]['perm'] = 700
    ref_table['%s/%s' % (tree_path, 'file3')]['hash'] = 'hash6'

    tree_str, tree_hash = MantraHashed.get_tree_contents(tree_path, dirs, files, ref_table)

    tree_lines = tree_str.split('\n')
    assert(tree_lines[0] == '700 tree hash1 folder1 ')
    assert(tree_lines[1] == '700 tree hash2 folder2 ')
    assert(tree_lines[2] == '700 file hash4 file1 ')
    assert(tree_lines[3] == '700 file hash5 file2 ')
    assert(tree_lines[4] == '700 file hash6 file3 ')

    assert(tree_hash == 'b258eeaf5c932c3b57a0e1f955f11331df5b66f6a1dfb470686397f6c3726c4c')