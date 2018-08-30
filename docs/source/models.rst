Models
########

.. image:: tensorflow.png
   :height: 30px
   :align: left

.. image:: pytorch.png
   :height: 30px
   :align: left

.. image:: keras.png
   :height: 30px
   :align: left

.. raw:: html

   <div style="clear: both;"></div>

**Mantra** models allow you to take a model in an framework such as TensorFlow or PyTorch, and enables them to be easily trained, deployed, evaluated, and more. In these docs we are going to see how we make a model package.


🤖 Make a Model
**********************

Go to the root of your project. To make a dataset use the :code:`makemodel` command. We can make a new model as follows:

.. code-block:: console

   $ mantra makemodel my_model

If we intend to use a particular framework, we can reference it upon creation:

.. code-block:: console

   $ mantra makemodel my_model --framework tensorflow

.. code-block:: console

   $ mantra makemodel my_model --framework keras

.. code-block:: console

   $ mantra makemodel my_model --framework pytorch

Our new model folder will be located at **myproject/models/my_model**. Inside:

.. code-block:: console

   __init__.py
   model.py
   README.md
   requirements.txt

- :code:`model.py` contains the core :code:`BaseModel` type class that wraps around your model
- :code:`requirements.txt` is where you can record any Python requirements for your model

We are now going to walk through some example models for the MNIST dataset for each framework.

🔢 Example: Keras on MNIST
******************************

In the previous chapter on Datasets, we made an MNIST dataset. We are now going to see how we can use this dataset to train a model.

Let's make a model using keras, we can make the project as follows:

.. code-block:: console

   $ mantra makemodel my_model --framework keras

Now let's open the :code:`model.py` file:

.. code-block:: python

  import tensorflow as tf

  from mantraml.models.KerasModel import KerasModel

  class MyKerasModel(KerasModel):

      def __init__(self, args=None, dataset=None, settings=None, **kwargs):
          super().__init__(args=args, dataset=dataset, settings=settings, **kwargs)

      def build_model(self):
          return

Our model inherits from the :code:`KerasModel` class. This gives us access to some predefined methods and attributes for Keras, as well as Mantra integration that allows our model to be easily trained, monitored and so on.

Let's build a basic neural network classifier in the build_model section:

.. code-block:: python

  import tensorflow as tf

  from mantraml.models.KerasModel import KerasModel

  class MyClassifier(KerasModel):

      def __init__(self, args=None, dataset=None, settings=None, **kwargs):
          super().__init__(args=args, dataset=dataset, settings=settings, **kwargs)

      def build_model(self):

          model = tf.keras.models.Sequential([
            tf.keras.layers.Flatten(),
            tf.keras.layers.Dense(512, activation=tf.nn.relu),
            tf.keras.layers.Dropout(0.2),
            tf.keras.layers.Dense(10, activation=tf.nn.softmax)
          ])

          return model

Now we can train with one line of code locally or via the cloud:

.. code-block:: console

   $ mantra train my_model --dataset mnist_png --cloud


MNIST is a well-known deep learning dataset containing handwritten numbers. We can download the tar.gz file `here <https://github.com/myleott/mnist_png/blob/master/mnist_png.tar.gz>`_.

Once you have downloaded the dataset, make a new data folder in your Mantra project by running the following command, refering the path of the tar file: 

.. code-block:: console

   $ mantra makedata mnist_png --tar mnist_png.tar.gz

The tar file contains 10 folders for each number, with png images enclosed. We want to extract the paired images and labels. First let's quickly example the class variables in :code:`data.py`. We want labels so :code:`has_labels` should be set to True. Likewise, :code:`data_type` should be set to 'png-images'; this is optional, but it gives us some extra methods for free in case we want to use them later.

At any time we can run the following command to test our new dataset:

.. code-block:: console

   $ mantra test mnist_png

This is optional but it performs some basic checks to see if anything is glaringly wrong. It can also be used to guide your development by telling you what to build next. If we run it on the current class, we are told:

.. code-block:: console

   AssertionError: Your extract_inputs() method returns None.

   This probably means you have not written an extract_inputs class method for your Dataset class.

   This method should return an np.ndarray containing the input data X.

As the test suggests, we need to actually extract some data! So let's do that. Below we've filled in the :code:`extract_inputs()` and :code:`extract_outputs()` methods to get the MNIST data. The path where your data is extracted is located at :code:`self.extract_dir`.

.. code-block:: python

   class MNIST(Dataset):

       name = 'mnist_png'
       tar_name = 'mnist_png' # e.g 'example_images' for 'example_images.tar.gz'
       data_type = 'png-images' # optional labelling of the datatype for free methods - see Mantra docs
       has_labels = True

       def __init__(self, name, **kwargs):       
           super().__init__(name=name, **kwargs)

       def extract_folders(self, training=True):
         
           number_folders = [f.path for f in os.scandir(self.extract_dir + folder) if f.is_dir()] 

           # loop over each folder (which contains each label)
           for folder in number_folders:
               folder_number = int(folder.split('/')[-1])
               images = glob.glob(os.path.join(folder, '*%s' % self.file_format))
               image_data = (np.array([scipy.misc.imread(image).astype(np.float) for image in images]) / 127.5) - 1.0
               labels = np.ones(image_data.shape[0])*folder_number

               if hasattr(self, 'X'):
                   self.X = np.concatenate((self.X, image_data))
               else:
                   self.X = image_data

               if hasattr(self, 'y'):
                   self.y = np.concatenate((self.y, labels))
               else:
                   self.y = labels

       def extract_inputs(self, training=True):
          
           if not hasattr(self, 'y') and not hasattr(self, 'X'):
               self.extract_folders(training=training)

           return self.X

       def extract_outputs(self):
          
           if not hasattr(self, 'y') and not hasattr(self, 'X'):
               self.extract_folders(training=training)

           return self.y

To test the dataset we can run the test command:

.. code-block:: console

   $ mantra test mnist_png

.. code-block:: console

   [+] All tests passed

We can also call a built-in :code:`sample` method in a Notebook or Python script, which samples from the :math:`X` matrix:

.. code-block:: python3

   from data.mnist.data import MNIST

   dataset = MNIST(name='mnist_png')
   dataset.sample()

.. image:: Figure_1.png
   :width: 300px
   :height: 225px
   :scale: 75%

We can see that the images coming out of our extraction methods look reasonable!

Now that we've built a dataset, we can build models that can be used with it. Let's now turn to the modelling features of Mantra... ✨. 


- 🤖 `Get started with Mantra models <models.html>`_  
