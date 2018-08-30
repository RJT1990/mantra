<div align="center">
    <img src="docs/source/mantra_header.png">
</div>

-----------------------------------------

# Mantra: Modular Deep Learning

<div align="center">
<img width="500" src="docs/source/demo2.gif">
</div>


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
mantra train cifar_model --dataset cifar_10 --cloud 
```
🚂 During training, you can spin up the Mantra UI:

```console
mantra ui
```
<img src="docs/source/demo.gif">

## Installation

To install mantra, you can use pip:

```
pip install mantraml
```

Mantra is tested on Python 3.5+. 

### AWS Dependencies

You will need to install AWS CLI as a dependency. 

1. Login to AWS through a browser, click your name in the menubar and click My Security Credentials.

2. Create a new Access Key and make a note of the **Access Key ID** and **Secret Access Key**.

3. From terminal enter the following:

```console
johnsmith@computer:~$ pip install awscli
johnsmith@computer:~$ aws configure
```

Once prompted, enter your AWS details and your default region (e.g. *us-east-1*).

4. Now your credentials will be accessible by the **boto3** AWS SDK library, which will allow **Mantra** to be used to 
provision cloud instances on your request.

5. Use *mantra cloud* from your mantra project root to configure your cloud settings.

You should also ensure you are happy with the default instance settings in mantra - you can check this in the *settings.py* file in your project root. 

### Have Fun

Please train responsibly.
