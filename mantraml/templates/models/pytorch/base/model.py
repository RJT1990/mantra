import torch

from mantraml.models import MantraModel


class MyModel(MantraModel):
    model_name = "My PyTorch Model"
    model_image = "default.jpg"
    model_notebook = 'notebook.ipynb'
    model_tags = ['new']

    def __init__(self, data=None, task=None, **kwargs):

        self.data = dask
        self.task = task

        # Put any configurable hyperparameters here, e.g self.dropout = kwargs.get('dropout', 0.25)
        # Then from command line you can vary, e.g. mantra train my_model --dataset my_data --dropout 0.25
        # self.batch_size and self.epochs have been configured for you - no need to write these :)

    def run(self):
        """
        Put any code for your model here.

        You will need to use Mantra Torch callbacks to get the results linked with Mantra; see the docs. It's just a few lines
        of code you need to add - no big changes to what you'd usually write.
        """
        
        return

    def predict(self, X):
        """
        Put code that predicts here (optional - used in conjunction with evaluation scripts)
        """

        return