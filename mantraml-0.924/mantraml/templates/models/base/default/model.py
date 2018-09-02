import tensorflow as tf

from mantraml.models.BaseModel import BaseModel


class MyModel(BaseModel):
    """
    This class implements a Base Model 
    """

    model_name = "My Model"
    model_image = "default.jpg"
    model_notebook = 'notebook.ipynb'
    model_tags = ['new']

    def __init__(self, args=None, dataset=None, settings=None, trial=False, **kwargs):

        # Put any configurable hyperparameters here, e.g:
        #         self.dropout = float(kwargs.get('dropout', 0.25))

        # this method initialises dependencies such as the dataset and cloud integration through settings
        super().__init__(args=args, dataset=dataset, settings=settings, trial=trial, **kwargs)


    def run(self):
        """
        Put any code for your model here.
        """
        
        return