import os
import tensorflow as tf


def FileWriter(mantra_model, **kwargs):
    logs_dir = '%s/trials/%s/logs/' % (os.getcwd(), mantra_model.trial.trial_folder_name)
    return tf.summary.FileWriter(logs_dir, **kwargs)
