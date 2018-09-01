import matplotlib.pyplot as plt
import tensorflow as tf


class EvaluateTask:

    def __init__(self, mantra_model):

        if mantra_model.task:
            mantra_model.task.latest_loss = mantra_model.task.evaluate(mantra_model)

            print('%s: %s' % (mantra_model.task.evaluation_name, mantra_model.task.latest_loss))

            if hasattr(mantra_model.task, 'secondary_metrics'):

                mantra_model.task.secondary_metrics_values = {}

                for metric in mantra_model.task.secondary_metrics:
                    metric_result = getattr(mantra_model.task, metric)(mantra_model)
                    mantra_model.task.secondary_metrics_values[metric] = float(metric_result)
                    print('%s: %s' % (metric.capitalize(), metric_result))


class ModelCheckpoint:

    def __init__(self, mantra_model, session):

        saver = tf.train.Saver()  

        if mantra_model.task:
            mantra_model.task.latest_loss = mantra_model.task.evaluate(self)

            if not hasattr(mantra_model.task, 'best_loss'):
                mantra_model.task.best_loss = None
                mantra_model.task.best_loss = mantra_model.task.latest_loss

            if mantra_model.save_best_only:
                if mantra_model.task.latest_loss < mantra_model.task.best_loss:
                    self.saver.save(session, '%s/trials/%s/checkpoint/' % (os.getcwd(), mantra_model.trial.trial_folder_name))
                    mantra_model.task.best_loss = mantra_model.task.latest_loss
            else:
                self.saver.save(session, '%s/trials/%s/checkpoint/' % (os.getcwd(), mantra_model.trial.trial_folder_name))

        else:
            self.saver.save(session, '%s/trials/%s/checkpoint/' % (os.getcwd(), mantra_model.trial.trial_folder_name))


class SavePlot:

    def __init__(self, mantra_model, plt, plt_name='default.png'):

        path = '%s/trials/%s/media' % (os.getcwd(), mantra_model.trial.trial_folder_name)
        
        if not os.path.exists(path):
            os.makedirs(path)
        
        plt.savefig(path + "/%s" % plt_name)


class StoreTrial:

    def __init__(self, mantra_model, epoch):
        mantra_model.store_trial_data(epoch)

