import glob
import matplotlib.pyplot as plt
import numpy as np
import os, time, itertools, pickle
import tensorflow as tf
from termcolor import colored

import sys

from mantraml.models import MantraModel
from mantraml.models.tensorflow.summary import FileWriter
from mantraml.models.tensorflow.callbacks import ModelCheckpoint, EvaluateTask, StoreTrial, SavePlot


class RaGAN(MantraModel):
    """
    This class implements the RaGAN paper https://arxiv.org/pdf/1807.00734.pdf


    """
    
    model_name = 'Relativistic GAN 256x256'
    model_image = 'image.jpeg'
    model_tags = ['gan']
    model_arxiv_id = '1807.00734' 

    def __init__(self, data=None, task=None, **kwargs):

        self.data = data
        self.task = task

        # Configure GPU
        config = tf.ConfigProto()
        config.gpu_options.allow_growth = kwargs.get('allow_growth', True)
        config.gpu_options.per_process_gpu_memory_fraction = kwargs.get('per_process_gpu_memory_fraction', 0.90)
        
        if tf.get_default_session() is None:
            self.session = tf.InteractiveSession(config=config)
        else:
            self.session = tf.get_default_session()

        # Architecture Information
        self.z_shape = kwargs.get('z_shape', (128))
        self.n_strides = kwargs.get('n_strides', (2))
        self.learning_rate_gen = kwargs.get('learning_rate', 1e-4)
        self.learning_rate_dis = kwargs.get('learning_rate', 1e-4)
        self.beta_1 = kwargs.get('beta_1', 0.0)
        self.beta_2 = kwargs.get('beta_2', 0.9)

    def init_model(self):
        """
        This is a wrapper function for initiatilising the model, for example initialisation weights, or loading
        weights from a past checkpoint

        Returns
        -----------
        void - updates the model with initialisation variables
        """
        
        tf.global_variables_initializer().run()

        self.writer = FileWriter(mantra_model=self)
        self.summary = tf.summary.merge_all()
        self.writer.add_graph(self.session.graph)

    @staticmethod
    def leaky_relu_with_batchnorm(arg, training=False):
        """
        Implements a Leaky ReLU activation function, with batch normalization applied to the layer outputs
        
        
        Parameters
        -----------
        arg - tf.layers object
            A TensorFlow layer to apply BatchNorm and the activation to
            
        training - bool
            For batch normalization; if we are training, this should be True; else should be False
            
        Returns
        -----------
        tf.layer - with Leaky ReLU and BatchNorm applied
        """
        
        return tf.nn.leaky_relu(tf.layers.batch_normalization(arg, training=training))

    @staticmethod
    def relu_with_batchnorm(arg, training=False):
        """
        Implements a ReLU activation function, with batch normalization applied to the layer outputs
        
        
        Parameters
        -----------
        arg - tf.layers object
            A TensorFlow layer to apply BatchNorm and the activation to
            
        training - bool
            For batch normalization; if we are training, this should be True; else should be False
            
        Returns
        -----------
        tf.layer - with ReLU and BatchNorm applied
        """
        
        return tf.nn.relu(tf.layers.batch_normalization(arg, training=training))
      
    def generator(self, z, training=True, reuse=False):
        """
        This implements the Generator Architecture - can overload this method if desired; default is a 
        DCGAN inspired architecture
        
        Parameters
        -----------
        z - tf.placeholder
            Containing the random noise with which to generate the sample
            
        training - bool
            For batch normalization; if we are training, this should be True; else should be False
        
        reuse - bool
            We reuse the variable scope if we call this method twice
        
        Returns
        -----------
        tf.Tensor - a Tensor representing the generated (fake) image
        """

        with tf.variable_scope("generator", reuse=reuse):
            conv_1 = self.leaky_relu_with_batchnorm(tf.layers.conv2d_transpose(z, self.data.image_shape[0]*4, [4, 4], strides=(1, 1), padding='valid'), training=training)
            conv_2 = self.leaky_relu_with_batchnorm(tf.layers.conv2d_transpose(conv_1, self.data.image_shape[0]*2, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'), training=training)
            conv_3 = self.leaky_relu_with_batchnorm(tf.layers.conv2d_transpose(conv_2, self.data.image_shape[0], [4, 4], strides=(self.n_strides, self.n_strides), padding='same'), training=training)
            conv_4 = self.leaky_relu_with_batchnorm(tf.layers.conv2d_transpose(conv_3, self.data.image_shape[0]//2, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'), training=training)
            conv_5 = self.leaky_relu_with_batchnorm(tf.layers.conv2d_transpose(conv_4, self.data.image_shape[0]//4, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'), training=training)
            conv_6 = self.leaky_relu_with_batchnorm(tf.layers.conv2d_transpose(conv_5, self.data.image_shape[0]//8, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'), training=training)
            conv_7 = tf.nn.leaky_relu(tf.layers.conv2d_transpose(conv_6, self.data.image_shape[2], [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))
            x = tf.nn.tanh(conv_7)
            return x

    def discriminator(self, x, training=True, reuse=False):
        """
        This implements the Discriminator Architecture - can overload this method if desired; default is a DCGAN inspired architecture
        
        Parameters
        -----------
        x - tf.Tensor
            Containing the fake (or real) image data
            
        training - bool
            For batch normalization; if we are training, this should be True; else should be False
        
        reuse - bool
            We reuse the variable scope if we call this method twice
        
        Returns
        -----------
        tf.Tensor, tf.Tensor - representing the probability the image is true/fake, and the logits (unnormalized probabilities)
        """
        with tf.variable_scope("discriminator", reuse=reuse):
            conv_1 = tf.nn.leaky_relu(tf.layers.conv2d(x, self.data.image_shape[0]//8, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))
            conv_2 = self.leaky_relu_with_batchnorm(tf.layers.conv2d(conv_1, self.data.image_shape[0]//4, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))
            conv_3 = self.leaky_relu_with_batchnorm(tf.layers.conv2d(conv_2, self.data.image_shape[0]//2, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))
            conv_4 = self.leaky_relu_with_batchnorm(tf.layers.conv2d(conv_3, self.data.image_shape[0], [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))
            conv_5 = self.leaky_relu_with_batchnorm(tf.layers.conv2d(conv_4, self.data.image_shape[0]*2, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))
            conv_6 = self.leaky_relu_with_batchnorm(tf.layers.conv2d(conv_5, self.data.image_shape[0]*4, [4, 4], strides=(self.n_strides, self.n_strides), padding='same'))            
            conv_7 = tf.layers.conv2d(conv_6, 1, [4, 4], strides=(1, 1), padding='valid')
            d = tf.nn.sigmoid(conv_7)
            return d, conv_7

    def show_result(self, num_epoch, path = 'result.png'):
        """
        Full Credit: https://github.com/znxlwm/tensorflow-MNIST-GAN-DCGAN
        
        Code modified to have multiple channels.        
        """

        fixed_z_ = np.random.normal(0, 1, (25, 1, 1, self.z_shape))
        test_images = self.session.run(self.x_fake, {self.z: fixed_z_, self.training: False})

        size_figure_grid = 5
        fig, ax = plt.subplots(size_figure_grid, size_figure_grid, figsize=(32, 32))
        for i, j in itertools.product(range(size_figure_grid), range(size_figure_grid)):
            ax[i, j].get_xaxis().set_visible(False)
            ax[i, j].get_yaxis().set_visible(False)

        for k in range(size_figure_grid*size_figure_grid):
            i = k // size_figure_grid
            j = k % size_figure_grid
            ax[i, j].cla()
            ax[i, j].imshow(np.reshape(((test_images[k]+1)*127.5).astype(np.uint8), (self.data.image_shape[0], self.data.image_shape[0], self.data.n_color_channels)))

        label = 'Epoch {0}'.format(num_epoch)
        fig.text(0.5, 0.04, label, ha='center')

        SavePlot(mantra_model=self, plt=plt, plt_name='faces_epoch_%s.png' % num_epoch)
        plt.close()

    def create_loss_function(self):
        """
        This method creates the loss function for the model - here we use a RaGAN

        Returns
        -----------
        void - updates instance with loss function variables self.d_loss and self.g_loss
        """
        
        # Discriminator output - d is a vector of probabilities (standard GAN notation)
        d_real, d_real_logits = self.discriminator(self.x_real, self.training)
        d_fake, d_fake_logits = self.discriminator(self.x_fake, self.training, reuse=True)

        # Loss Functions
        
        d_loss_1 = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_real_logits - tf.reduce_mean(d_fake_logits), labels=tf.ones_like(d_real)))
        d_loss_2 = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_fake_logits - tf.reduce_mean(d_real_logits), labels=tf.zeros_like(d_fake)))
        g_loss_1 = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_real_logits - tf.reduce_mean(d_fake_logits), labels=tf.zeros_like(d_fake)))
        g_loss_2 = tf.reduce_mean(tf.nn.sigmoid_cross_entropy_with_logits(logits=d_fake_logits - tf.reduce_mean(d_real_logits), labels=tf.ones_like(d_real)))

        self.d_loss = d_loss_1 + d_loss_2
        self.g_loss = g_loss_1 + g_loss_2

    def define_logs(self):
        """
        Define terms to log here

        Returns
        ----------
        void - updates parameters
        """

        tf.summary.scalar("d_loss", self.d_loss)
        tf.summary.scalar("g_loss", self.g_loss)

    def create_optimizers(self):
        """
        This method creates the optimizers for the model - here we use ADAM optimizers.

        Returns
        -----------
        void - updates instance with optimizer variables self.d_optimizer and self.g_optimizer
        """

        # Differentiable Variables
        theta = tf.trainable_variables()
        theta_d = [var for var in theta if var.name.startswith('discriminator')]
        theta_g = [var for var in theta if var.name.startswith('generator')]
        
        # optimizer for each network
        with tf.control_dependencies(tf.get_collection(tf.GraphKeys.UPDATE_OPS)):
            self.d_optimizer = tf.train.AdamOptimizer(self.learning_rate_dis, beta1=self.beta_1, beta2=self.beta_2).minimize(self.d_loss, var_list=theta_d)
            self.g_optimizer = tf.train.AdamOptimizer(self.learning_rate_gen, beta1=self.beta_1, beta2=self.beta_2).minimize(self.g_loss, var_list=theta_g)
        
    def build_model(self):
        """
        This method constructs the model, including the loss function and optimization routine
        
        Returns
        -----------
        void - constructs model objects that are stored to the model instance
        """
        
        # Input Variables
        self.x_real = tf.placeholder(tf.float32, shape=(None, self.data.image_shape[0], self.data.image_shape[1], self.data.image_shape[2])) # for use of real image input
        self.z = tf.placeholder(tf.float32, shape=(None, 1, 1, self.z_shape)) # the random noise used to generate the images
        self.training = tf.placeholder(dtype=tf.bool) # boolean for batchnorm denoting that training is activated
        self.x_fake = self.generator(self.z, self.training) # fake input generated by the Generator Network

        # Discriminator and Generator Loss Functions
        self.create_loss_function()

        # Create Optimizers for Traing
        self.create_optimizers()

    def gradient_update(self, iter):
        """
        Updates the parameters with a single gradient update

        Parameters
        ----------
        iter - int
            The iteration number

        Returns
        ----------
        void - updates parameters
        """

        # Discriminator Update
        x = self.data.X[iter*self.batch_size:(iter+1)*self.batch_size]
        z = np.random.normal(0, 1, (self.batch_size, 1, 1, self.z_shape))

        discriminator_loss, _ = self.session.run([self.d_loss, self.d_optimizer], {self.x_real: x, self.z: z, self.training: True})

        # Generator Update
        z = np.random.normal(0, 1, (self.batch_size, 1, 1, self.z_shape))
        summary, generator_loss, _ = self.session.run([self.summary, self.g_loss, self.g_optimizer], {self.z: z, self.x_real: x, self.training: True})

        self.writer.add_summary(summary, iter)

    def end_of_epoch_update(self, epoch):
        """
        Update to apply at the end of the epoch
        """

        epoch_run_time = time.time() - self.epoch_start_time

        if epoch % 1 == 0:
            self.show_result((epoch + 1), path='')
            
    def end_of_training_update(self):
        """
        Update to apply at the end of training
        """

        self.session.close()

    def run(self):
        """
        Runs the training.
        """
        
        # Build and initialize
        self.build_model()

        if self.trial:
            self.define_logs()
                
        self.init_model()

        # Ready data
        self.batches_per_epoch = len(self.data) // self.batch_size
            
        # Results Dict
        np.random.seed(int(time.time())) # random seed for training
        
        for epoch in range(self.epochs):
            self.epoch_start_time = time.time()

            for iter in range(self.batches_per_epoch):
                self.gradient_update(iter)

            self.end_of_epoch_update(epoch)

            ModelCheckpoint(mantra_model=self, session=self.session)
            if self.task:
                EvaluateTask(mantra_model=self)
            StoreTrial(mantra_model=self, epoch=epoch)

            self.end_of_epoch_message(epoch=epoch, message=str(time.time() - self.epoch_start_time))

        self.end_of_training_update()