import tensorflow as tf


class FileWriter:

    def __init__(self, mantra_model, **kwargs):
        return tf.summary.FileWriter('%s/trials/%s/logs/' % (os.getcwd(), self.mantra_model), **kwargs)