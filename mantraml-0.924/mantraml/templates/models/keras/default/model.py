import tensorflow as tf

from mantraml.models.KerasModel import KerasModel


class MyKerasModel(KerasModel):
    """
    This class implements a Keras Model
    """

    model_name = "My Keras Model"
    model_image = "default.jpg"
    model_notebook = 'notebook.ipynb'
    model_tags = ['new']

    def __init__(self, args=None, dataset=None, settings=None, trial=False, **kwargs):

        # Put any configurable hyperparameters here, e.g:
        #         self.dropout = float(kwargs.get('dropout', 0.25))

        super().__init__(args=args, dataset=dataset, settings=settings, trial=trial, **kwargs)

        # We can overwrite Keras defaults defined in the KerasModel class, e.g.:
        #         self.optimizer = kwargs.get('optimizer', 'adam')
        #         self.loss = kwargs.get('loss', 'categorical_crossentropy')

    def build_model(self):
        # Put your code for constructing the architecutre of the model here - should return a keras model object
        # this model will be saved in self.model
        return

    def predict(self, X):
        # Optional, but can write a predict method that you can call in an evaluation script.
        # e.g. return self.model.predict(X)
        return