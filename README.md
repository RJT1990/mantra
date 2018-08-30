# Mantra

The Mantra Library

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

