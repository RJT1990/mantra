from mantraml.tasks import Task


class MyTask(Task):
    task_name = 'My Example Task'
    evaluation_name = 'My Evaluation Metric'
    training_split = (0.5, 0.25, 0.25)

    def evaluate(self, model):
        # Return an evaluation metric scalar here. For example, categorical cross entropy on the validation set:
        # predictions = model.predict(self.X_val)
        # return -np.nansum(self.y_val*np.log(predictions) + (1-self.y_val)*np.log(1-predictions)) / predictions.shape[0]
        return