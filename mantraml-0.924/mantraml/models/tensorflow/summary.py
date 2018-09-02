import os
import tensorflow as tf


def FileWriter(mantra_model, **kwargs):
    return tf.summary.FileWriter('%s/trials/%s/logs/' % (os.getcwd(), mantra_model.trial.trial_folder_name), **kwargs)