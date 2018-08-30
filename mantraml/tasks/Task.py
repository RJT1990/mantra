
class Task:
    """
    This class defines an task procedure 
    """

    def __init__(self, data):
        """
        Parameters
        -----------

        data - Dataset class
            Containing the data to be assigned to the task
        """

        self.data = data

        self.test_data = None
        self.training_data = None

    def get_test_data(self):
        """
        Get the test data for the task
        """

        if self.test_data is not None:
            return self.test_data

        self.test_data = None, None

        if self.data.y is not None:
            if self.training_test_split is not None:
                end_index = int(self.training_test_split*len(self.data))
                self.test_data = self.data.X[end_index:], self.data.y[end_index:]
            elif self.training_indices is not None:
                test_indices = list(set(list(range(len(data)))) - set(self.training_indices))
                self.test_data = self.data.X[test_indices], self.data.y[test_indices]

        else:
            if self.training_test_split is not None:
                end_index = int(self.training_test_split*len(self.data))
                self.test_data = self.data.X[end_index:], None
            elif self.training_indices is not None:
                test_indices = list(set(list(range(len(data)))) - set(self.training_indices))
                self.test_data = self.data.X[test_indices], None
        
        return self.test_data

    def get_training_data(self):
        """ 
        Get the training data for the task 
        """

        if self.training_data is not None:
            return self.training_data

        self.training_data = None, None

        if self.data.y is not None:
            if self.training_test_split is not None:
                end_index = int(self.training_test_split*len(self.data))
                self.training_data = self.data.X[:end_index], self.data.y[:end_index]
            elif self.training_indices is not None:
                self.training_data = self.data.X[self.training_indices], self.data.y[self.training_indices]                
        else:
            if self.training_test_split is not None:
                end_index = int(self.training_test_split*len(self.data))
                self.training_data = self.data.X[:end_index], None
            elif self.training_indices is not None:
                self.training_data = self.data.X[self.training_indices], None

        return self.training_data