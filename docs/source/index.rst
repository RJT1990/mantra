.. mantraml documentation master file, created by
   sphinx-quickstart on Thu Jul 19 11:05:32 2018.
   You can adapt this file completely to your liking, but it should at least
   contain the root `toctree` directive.

Mantra : A Deep Learning Development Kit
##########################################

.. image:: demo.gif
   :width: 600px
   :scale: 100 %
   :align: center

**Mantra** is a deep learning development kit that manages the various components in an deep learning project, and makes it much easier to do routine tasks like training in the cloud, model monitoring, model benchmarking and more. It works with your favourite deep learning libraries like TensorFlow, PyTorch and Keras.

You might like mantra if:

* You need to structure deep learning projects: versioning, monitoring and storage.
* You need devops tasks like cloud integration and file syncing taken care for you.
* You need to evaluate your model against benchmark tasks, e.g. CIFAR-10 accuracy.


🌍 Installation
**********************

Mantra is a Python that you can install via pip:

.. code-block:: console

   $ pip install mantraml

It is currently tested on Python 3.5-7. 

Additional dependencies you need to install are TensorFlow or PyTorch depending on which framework you want to use. If you want to use the TensorBoard feature of Mantra with PyTorch then you should also install TensorboardX.


🚀 Get Started
***************************************

Find a directory where you want to create a project and run:

.. code-block:: console

   $ mantra launch my_project_name

This will create a **my_project_name** directory with a folder structure like this:

.. code-block:: console

   data/
   models/
   tasks/
   trials/
   __init__.py
   mantra.yml
   README.md
   settings.py

- The :code:`data/` folder contains your datasets
- The :code:`models/` folder contains your models
- The :code:`tasks/` folder contains your tasks
- The :code:`trials/` folder contains trial data (data when you train a model)
- The :code:`mantra.yml` file contains project metadata
- The :code:`settings.py` file contains project settings

Now we have a project! To view the current project through the Mantra UI, execute the following from your project root:

.. code-block:: console

   $ mantra ui

Now that you are ready, it's time to learn how Mantra models and datasets work!

- 🤖 `Get started with Mantra models <models.html>`_
- 💾 `Get started with Mantra datasets <datasets.html>`_ 
- 🏃 `Get started with Mantra tasks <tasks.html>`_
- 🎁 `Get started with Mantra training <training.html>`_

.. toctree::
   :maxdepth: 2
   :hidden:

   models
   datasets
   tasks
   training
