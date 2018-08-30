<div align="center">
    <img src="https://image.ibb.co/mZYxJU/mantranew.png">
  
  
</div>

-----------------------------------------

# Mantra: Modular Deep Learning

**Mantra** is a deep learning development kit that manages the various components in an deep learning project, and makes it much easier to do routine tasks like training in the cloud, model monitoring, model benchmarking and more. It works with your favourite deep learning libraries like TensorFlow, PyTorch and Keras. 

You might like mantra if:

- You need a way to structure your deep learning projects: versioning, monitoring and storage of models and data.
- You need boring devops tasks like cloud integration and file syncing between cloud/local taken care for you.
- You need a way to easily compare and evaluate your model against benchmark tasks, e.g. accuracy on CIFAR-10.

Read the docs <a href="">here</a>. This is an alpha release: give us your huddled masses of issues and pull requests!

## Design Principles

Mantra is based on the idea of a data-model-task (DMT) design pattern, the idea being that most machine learning projects involve these core components. This design pattern facilitates:

- **Loose Coupling** : Datasets, models and tasks need not be tightly coupled. It should be easy to swap out components without rewriting code or configuring folders; for example, a GAN model should *just work* with any image dataset. With Mantra, there is no setup required: you can train a new model on an existing dataset or task straight away.

- **Easy to Modify** : A lot of deep learning logic lives in single, big scripts, making it hard to extract the specific features of interest - e.g. everything related to data augmentation, or code related to a specific architectural feature. Mantra's modular code allows you to more easily take what we want and apply it in new contexts.

- **Cohesiveness** : What use is a dataset for machine learning if it doesn't come with data processing logic? Mantra bundles artefacts like raw data files and data processing code together, so you are never left to do any work stitching things like datasets and models together.

## Get Started 

🚀 To launch your first Mantra project, execute the following to create a new project directory:

```console
mantra launch my_project 
```
☁ Configure your cloud settings and API keys:

```console
mantra cloud 
```
🤖 To train the example CNN model on CIFAR-10 with your cloud provider:

```console
mantra train cnn_model --dataset cifar_10 --cloud 
```

🚂 During training, you can spin up the Mantra UI:

```console
mantra ui
```

## AWS Setup

1. Press your name (e.g. "John Smith") in the menubar and click My Security Credentials.

2. Create a new Access Key and make a note of the **Access Key ID** and **Secret Access Key**.

3. From terminal enter the following:

```console
johnsmith@computer:~$ pip install awscli
johnsmith@computer:~$ aws configure
```

Once prompted, enter your AWS details and your default region (e.g. *us-east-1*).

4. Now your credentials will be accessible by the **boto3** AWS SDK library, which will allow **Mantra** to be used to 
provision cloud instances on your request.

5. Once you start an Mantra project (see below) change your projects settings.py file and set the **AWS_KEY_NAME** and **AWS_KEY_PATH** fields - these will determine the credentials of any new instances you create through Mantra.

## Getting Started

Clone the repository and then in the root of the project:

```console
python setup.py install
```

🚀 To launch your first Mantra project, execute the following to create a new project directory:

```console
mantra launch my_project 
```

🤖 If you want to create a new model, then execute the following from the root of your project directory:

```console
mantra makemodel my_new_model
```

💾 If you want to create a new dataset, then execute the following from the root of your project directory:

```console
mantra makedata my_new_dataset
```

