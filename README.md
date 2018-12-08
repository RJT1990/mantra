<div align="center">
    <img width="250" src="docs/source/logo.png">    
</div>

-----------------------------------------

[![CircleCI](https://circleci.com/gh/RJT1990/mantra.svg?style=shield&circle-token=ef9ddee091dd77395273f8d59f6b6b5b091212c7)](https://circleci.com/gh/RJT1990/mantra)
[![PyPI version](https://badge.fury.io/py/mantraml.svg)](https://badge.fury.io/py/mantraml)
[![Gitter chat](https://badges.gitter.im/gitterHQ/gitter.png)](https://gitter.im/mantraml/Lobby)
[![Documentation Status](https://readthedocs.org/projects/mantra/badge/?version=latest)](http://mantra.readthedocs.io/en/latest/?badge=latest)


**mantra** is a rapid development framework for deep learning. 

**Problem**: Every ML project needs a way to train, track and share models. But every project does it in a different way with a lot of boilerplate code being needlessly reinvented. 

**Solution**: mantra is a framework for writing dataset and model classes that enables single line training, has a tracking UI, and makes it easy to encapsulate and share results. 

**Key Features**:

- Boilerplate classes for common dataset and model types
- Command-line interface for training with parameter parsing
- Automatic provisioning of cloud instances for remote training
- UI for monitoring training, comparing experiments and storing media
- Encapsulation of datasets and models by design, enabling easy sharing 

This is an alpha release. All contributions are welcome - see [here](https://github.com/RJT1990/mantra/blob/master/CONTRIBUTING.md) for guidelines on how to contribute.

[You can read the docs here](http://mantra.readthedocs.io/en/latest/).

-----------------------------------------

<div align="center">
<img src="docs/source/demo.gif">
</div>
<br><br>

## Get Started 

🚀 To launch your first Mantra project, execute the following to create a new project directory:

```console
mantra launch my_project 
```
☁ Configure your cloud settings and API keys:

```console
cd my_project 
mantra cloud 
```
💾 Get the example datasets and models from [here](https://github.com/RJT1990/mantra-examples):
 
```console
mantra import https://github.com/RJT1990/mantra-examples.git
``` 

🤖 Here is an example model you can train:

```console
mantra train relativistic_gan --dataset decks --cloud --dev --image-dim 256 256
```

🚂 During training, you can spin up the Mantra UI to track the progress:

```console
mantra ui
```

## Installation

To install mantra, you can use pip:

```
pip install mantraml
```
You should also have TensorFlow or PyTorch installed depending on which framework you intend to use.

Mantra is tested on Python 3.5+. It is not currently supported on Windows.

### Have Fun

> Arise! Awake! Approach the great and learn.
