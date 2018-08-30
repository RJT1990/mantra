DATA_TEST_MSGS = {}


DATA_TEST_MSGS['empty_inputs'] = '''Your extract_inputs() method returns None.

This probably means you have not written an extract_inputs class method for your Dataset class.

This method should return an np.ndarray containing the input data X.'''


DATA_TEST_MSGS['non_numpy_input'] = '''Your extract_inputs() method does not return a np.array.

In order to process your data, the models should take in np.ndarrays of data.

Rewrite your method so it return an np.ndarray containing the input data X.'''


DATA_TEST_MSGS['zero_len_input'] = '''Your extract_inputs() method returns an np.array that is empty.

Rewrite your method so it return an np.ndarray containing some non-empty input data X.'''


DATA_TEST_MSGS['zero_std_input'] = '''Your extract_inputs() method returns an np.array that has zero variation.

Rewrite your method so it return an np.ndarray containing some varying input data X.'''


DATA_TEST_MSGS['input_contains_nans'] = '''Warning: Your extract_inputs() method returns an np.array with nans.

Your algorithm may support missing data, but if it does not, you may want to investigate this.'''


DATA_TEST_MSGS['empty_outputs'] = '''Your extract_output() method returns None, but the has_labels attribute of your DataSet class is set to TRUE.

This means that you will be trying to access labels that don't exist!

Either turn has_labels to FALSE if you don't require labels - e.g. for generative models - or fix the method so it returns an np.ndarray of output data y.
'''

DATA_TEST_MSGS['non_numpy_output'] = '''Your extract_outputs() method does not return a np.array.

In order to process your data, the models should take in np.ndarrays of data.

Rewrite your method so it return an np.ndarray containing the output data y.'''


DATA_TEST_MSGS['empty_outputs_and_no_flag'] = '''Your extract_output() method returns None. This may not be a problem if you do not need/have labels. In which case, define a class variable in your dataset has_labels and set this to FALSE.

If you do need labels, then you will need to define an extract_output method. This should return an np.ndarray of output data y.'''


DATA_TEST_MSGS['zero_len_output'] = '''Your extract_outputs() method returns an np.array that is empty.

Rewrite your method so it return an np.ndarray containing some non-empty output data y.'''


DATA_TEST_MSGS['zero_std_output'] = '''Your extract_outputs() method returns an np.array that has zero variation.

Rewrite your method so it return an np.ndarray containing some varying output data y.'''


DATA_TEST_MSGS['output_contains_nans'] = '''Warning: Your extract_outputs() method returns an np.array with nans.

Your algorithm may support missing data, but if it does not, you may want to investigate this.'''


DATA_TEST_MSGS['input_output_lens'] = '''Your output data length (%s) is different from your input data length (%s).

Ensure that they have the same number of examples.'''
