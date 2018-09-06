import matplotlib.pyplot as plt
import os
import torch


class EvaluateTask:

    def __init__(self, mantra_model):

        task = mantra_model.task

        if task:
            task.latest_loss = task.evaluate(mantra_model)

            print('%s: %s' % (task.evaluation_name, task.latest_loss))

            if hasattr(mantra_model.task, 'secondary_metrics'):

                task.secondary_metrics_values = {}

                for met in task.secondary_metrics:
                    metric_result = getattr(task, met)(mantra_model)
                    task.secondary_metrics_values[met] = float(metric_result)
                    print('%s: %s' % (met.capitalize(), metric_result))


class ModelCheckpoint:

    def __init__(self, mantra_model, torch_model):

        checkpoint_dir = '%s/trials/%s/checkpoint/' % (os.getcwd(), mantra_model.trial.trial_folder_name)

        if not os.path.isdir(checkpoint_dir):
            os.makedirs(checkpoint_dir)

        if mantra_model.task:
            mantra_model.task.latest_loss = mantra_model.task.evaluate(self)

            if not hasattr(mantra_model.task, 'best_loss'):
                mantra_model.task.best_loss = None
                mantra_model.task.best_loss = mantra_model.task.latest_loss

            if mantra_model.save_best_only:
                if mantra_model.task.latest_loss < mantra_model.task.best_loss:
                    torch.save(torch_model.state_dict(), '%s/trials/%s/checkpoint/model_weights.pt' % (os.getcwd(), mantra_model.trial.trial_folder_name))
                    mantra_model.task.best_loss = mantra_model.task.latest_loss
            else:
                torch.save(torch_model.state_dict(), '%s/trials/%s/checkpoint/model_weights.pt' % (os.getcwd(), mantra_model.trial.trial_folder_name))

        else:
            torch.save(torch_model.state_dict(), '%s/trials/%s/checkpoint/model_weights.pt' % (os.getcwd(), mantra_model.trial.trial_folder_name))


class SavePlot:

    def __init__(self, mantra_model, plt, plt_name='default.png'):
        path = '%s/trials/%s/media' % (os.getcwd(), mantra_model.trial.trial_folder_name)  

        if not os.path.exists(path):
            os.makedirs(path)

        plt.savefig(path + "/%s" % plt_name)


class StoreTrial:

    def __init__(self, mantra_model, epoch):
        mantra_model.store_trial_data(epoch)
