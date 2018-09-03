
class Task:
    """
    This class contains methods and attributes for extracting relevant subsets of a Dataset for a class.
    For example, you might have a training, validation test split and want to refer to these subsets
    specifically when performing training.
    """

    def __init__(self, data):
        """
        Parameters
        -----------
        data - mantra Dataset class
            Containing the data to be assigned to the task
        """

        self.data = data

        self.training_data = None
        self.validation_data = None
        self.test_data = None

        if not hasattr(self, 'training_split'):
            self.training_split = None

        if not hasattr(self, 'training_indices'):
            self.training_indices = None

        if not hasattr(self, 'validation_indices'):
            self.validation_indices = None

        if not hasattr(self, 'test_indices'):
            self.test_indices = None

        self._X_train = None
        self._y_train = None
        self._X_val = None
        self._y_val = None
        self._X_test = None
        self._y_test = None

    @property
    def X_train(self):
        """
        Obtains the training data features X

        Returns
        --------
        np.ndarray of feature data        
        """

        if self._X_train is not None:
            return self._X_train

        self._X_train, self._y_train = self.get_training_data()

        return self._X_train

    @property
    def y_train(self):
        """
        Obtains the training data labels y

        Returns
        --------
        np.ndarray of feature data        
        """

        if self._y_train is not None:
            return self._y_train

        self._X_train, self._y_train = self.get_training_data()

        return self._y_train

    @property
    def X_val(self):
        """
        Obtains the validation data features X

        Returns
        --------
        np.ndarray of feature data        
        """

        if self._X_val is not None:
            return self._X_val

        self._X_val, self._y_val = self.get_validation_data()

        return self._X_val

    @property
    def y_val(self):
        """
        Obtains the validation data labels y

        Returns
        --------
        np.ndarray of label data        
        """

        if self._y_val is not None:
            return self._y_val

        self._X_val, self._y_val = self.get_validation_data()

        return self._y_val

    @property
    def X_test(self):
        """
        Obtains the test data features X

        Returns
        --------
        np.ndarray of feature data        
        """

        if self._X_test is not None:
            return self._X_test

        self._X_test, self._y_test = self.get_test_data()

        return self._X_test

    @property
    def y_test(self):
        """
        Obtains the test data labels y

        Returns
        --------
        np.ndarray of label data        
        """

        if self._y_test is not None:
            return self._y_test

        self._X_test, self._y_test = self.get_test_data()

        return self._y_test

    def get_training_data(self):
        """ 
        Get the training data for the task 
        """

        if self.training_data is not None:
            return self.training_data

        self.training_data = None, None

        if self.data.y is not None:
            if self.training_split is not None:
                end_index = int(self.training_split[0]*len(self.data))
                self.training_data = self.data.X[:end_index], self.data.y[:end_index]
            elif self.training_indices is not None:
                self.training_data = self.data.X[self.training_indices], self.data.y[self.training_indices]                
        else:
            if self.training_split is not None:
                end_index = int(self.training_split[0]*len(self.data))
                self.training_data = self.data.X[:end_index], None
            elif self.training_indices is not None:
                self.training_data = self.data.X[self.training_indices], None

        return self.training_data

    def get_test_data(self):
        """
        Get the test data for the task
        """

        if self.test_data is not None:
            return self.test_data

        self.test_data = None, None

        if self.data.y is not None:
            if self.training_split is not None:
                start_index = int(sum(self.training_split[:2])*len(self.data))
                self.test_data = self.data.X[start_index:], self.data.y[start_index:]
            elif self.test_indices is not None:
                self.test_data = self.data.X[self.test_indices], self.data.y[self.test_indices]  

        else:
            if self.training_split is not None:
                start_index = int(sum(self.training_split[:2])*len(self.data))
                self.test_data = self.data.X[start_index:], None
            elif self.test_indices is not None:
                self.test_data = self.data.X[self.test_indices], None
        
        return self.test_data

    def get_validation_data(self):
        """ 
        Get the validation data for the task 
        """

        if self.validation_data is not None:
            return self.validation_data

        self.validation_data = None, None

        if self.data.y is not None:
            if self.training_split is not None:
                start_index = int(self.training_split[0]*len(self.data))
                end_index = int(sum(self.training_split[:2])*len(self.data))
                self.validation_data = self.data.X[start_index:end_index], self.data.y[start_index:end_index]
            elif self.validation_indices is not None:
                self.validation_data = self.data.X[self.validation_indices], self.data.y[self.validation_indices]                
        else:
            if self.training_split is not None:
                start_index = int(self.training_split[0]*len(self.data))
                end_index = int(sum(self.training_split[:2])*len(self.data))
                self.validation_data = self.data.X[start_index:end_index], None
            elif self.validation_indices is not None:
                self.validation_data = self.data.X[self.validation_indices], None

        return self.validation_data