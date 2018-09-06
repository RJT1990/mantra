import os
import tensorboardX


def SummaryWriter(mantra_model, **kwargs):
    trial_folder_name = mantra_model.trial.trial_folder_name
    trial_logs_path = '%s/trials/%s/logs/' % (os.getcwd(), trial_folder_name)
    return tensorboardX.SummaryWriter(trial_logs_path, **kwargs)
