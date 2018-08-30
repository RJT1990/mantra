Training
########

Once you have encapsulated your datasets and models, you can easily train them on any infrastructure.

🏃 Training on AWS
**********************

To train a model on AWS, first configure your AWS credentials

.. code-block:: console

   $ mantra config aws

You will be asked for your API keys, default zone, instance type and S3 bucket.

We use S3 as the central storage backend for all of your files.

To train :code:`mymodel` using :code:`mydataset` from the console:

.. code-block:: console

   $ mantra train --dataset mydataset mymodel

   # or in python:
   mymodel.train(mydata)


This will provision a new AWS EC2 instance to match your development environment, sync over the datasets and models (via S3) and run the training.

The instance will be automatically shut down after 15 minutes of inactivity, and all files stored in S3.

To re-use the instance pass the instance hash or name as a parameter:

.. code-block:: console

   $ mantra train --dataset mydataset mymodel --instance i-123456789

   # or in python
   mymodel.train(mydata, instance="i-123456789")


🏃 Training on your own machines over SSH
********************************************

If you manage your own machines, you can use them for remote training.

.. code-block:: console

   $ mantra config ssh

You will be asked for the location of your private key, default instance and a host:directory where the files should be permanently stored.

After that you can train your model by specifying the IP address of your machine:

.. code-block:: console

   $ mantra train --dataset mydataset mymodel --host <ip address>

   # or in python
   mymodel.train(mydata, host="<ip address>")


👀 Meet all the training options
***************************************

All options are available through the commandline (:code:`mantra train`) and the python interface (:code:`Model.train()`).

.. py:method:: Model.train(dataset, instance, host, batch_size, epochs, save_model, use_checkpoint, **kwargs)

 **Parameters**

 .. py:attribute:: dataset

  The dataset object used for training.

 .. py:attribute:: instance

  The Cloud instance ID to be used. If no instance and host are specified, the training is local.

 .. py:attribute:: host

  IP address of the host to use. The host is assumed to have installed the correct software dependencies.

 .. py:attribute:: batch_size

  The size of a training batch, in number of datapoints.

 .. py:attribute:: epochs

  Number of epochs to use for training

 .. py:attribute:: save_model

  If to save the model or not.

 .. py:attribute:: use_checkpoint

  If to save the checkpoints or not.

 .. py:attribute:: kwargs

  Any other parameters to be passed to the train function. All of these will be automatically captured and attached to the training run. When using on a commandline use as :code:`--kwargs "param1=10,param2=10"`.






