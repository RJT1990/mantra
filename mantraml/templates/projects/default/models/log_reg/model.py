import tensorflow

from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Dropout, Activation, Flatten
from tensorflow.keras.layers import Conv2D, MaxPooling2D

from mantraml.models import MantraModel
from mantraml.models.keras.callbacks import TensorBoard, StoreTrial, EvaluateTask, ModelCheckpoint


class LogisticRegression(MantraModel):
    """
    A simple Logistic Regression
    """

    model_name = "Logistic Regression"
    model_image = "default.png"
    model_notebook = 'notebook.ipynb'
    model_tags = ['logistic', 'regression']

    def __init__(self, data=None, task=None, **kwargs):
        self.data = data
        self.task = task

        self.optimizer = kwargs.get('optimizer', 'adam')
        self.loss = kwargs.get('loss', 'binary_crossentropy')
        self.metrics = kwargs.get('metrics', ['accuracy'])
        self.loss_weights = kwargs.get('loss_weights', None)
        self.sample_weight_mode = kwargs.get('sample_weight_mode', None)
        self.weighted_metrics = kwargs.get('weighted_metrics', None)
        self.target_tensors = kwargs.get('target_tensors', None)
   
    def run(self):
        """
        Runs the training
        """
        
        model = Sequential()
        model.add(Dense(1, input_dim=self.data.X.shape[1], kernel_initializer='normal'))
        model.add(Activation('sigmoid'))

        model.compile(
            loss=self.loss,
            optimizer=self.optimizer,
            metrics=self.metrics,
            loss_weights=self.loss_weights,
            sample_weight_mode=self.sample_weight_mode,
            weighted_metrics=self.weighted_metrics,
            target_tensors=self.target_tensors)

        self.model = model
        
        tb_callback = TensorBoard(mantra_model=self, histogram_freq=0, write_graph=True, write_images=True)
        exp_callback = StoreTrial(mantra_model=self)
        eval_callback = EvaluateTask(mantra_model=self)
        checkpoint_callback = ModelCheckpoint(mantra_model=self)

        callbacks = [tb_callback, eval_callback, checkpoint_callback, exp_callback]

        if self.task:
            X = self.task.X_train
            y = self.task.y_train
        else:
            X = self.data.X
            y = self.data.y

        self.model.fit(X, y, epochs=self.epochs, batch_size=self.batch_size, callbacks=callbacks)

    def predict(self, X):
        return self.model.predict(X)
