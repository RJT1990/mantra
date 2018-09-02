import os
import tensorboardX

def SummaryWriter(mantra_model, **kwargs):
    return tensorboardX.SummaryWriter('%s/trials/%s/logs/' % (os.getcwd(), mantra_model.trial.trial_folder_name), **kwargs)