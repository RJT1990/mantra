import tensorflow as tf

from mantraml.models.TFModel import TFModel


class MyTensorFlowModel(TFModel):
    """
    This class implements a TensorFlow model
    """

    model_name = "My TensorFlow Model"
    model_image = "default.jpg"
    model_notebook = 'notebook.ipynb'
    model_tags = ['new']

    def __init__(self, session=None, args=None, dataset=None, settings=None, trial=False, **kwargs):
        """
        Parameters
        -----------

        session - tf.Session() object
            A TensorFlow Session - can leave empty, in which case a default session is found or InteractiveSession is initialized
            
        args - command line args
            Arguments from the Mantra command line 

        dataset - mantraml.Dataset type object 
            A mantraml.Dataset like object that contains the data and data processing

        settings - Python module
            Containing user settings (including cloud options)

        trial - bool
            If True, will conduct a trial and configure storage for it

        **kwargs - use for training and architecture information (see below)
        """

        # Put any configurable hyperparameters here, e.g:
        #         self.dropout = float(kwargs.get('dropout', 0.25))

        # this method initialises dependencies such as the dataset and cloud integration through settings
        super().__init__(session=session, args=args, dataset=dataset, settings=settings, trial=trial, **kwargs)

    def build_model(self):
        """
        This method constructs the model, including the loss function and optimization routine
        
        Returns
        -----------
        void - constructs model objects that are stored to the model instance
        """
        
        # Put your code for constructing the architecutre of the model here
        return

    def gradient_update(self, iter):
        """
        Updates the parameters with a single gradient update

        Parameters
        ----------
        iter - int
            The iteration number

        Returns
        ----------
        void - updates parameters
        """

        # Put your code for performing the gradient update here
        return

    def end_of_epoch_update(self, epoch):
        """
        Update to apply at the end of the epoch
        """

        # Put any code for the end of an epoch here
        return

    def end_of_training_update(self):
        """
        Update to apply at the end of training
        """

        # Put any code to be executed at the end of training here
        return