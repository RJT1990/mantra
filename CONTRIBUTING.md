# Contributing to Mantra

**Mantra** is a community effort and everyone is welcome to contribute. **We are especially welcoming to first-time open source contributors**: we know that it can be intimidating getting started in open source, so feel free to use our project as a stepping stone into open source development!

We abide by the principles of the [Python Software Foundation](https://www.python.org/psf/codeofconduct/): openness, consideration and respect.

To get started, read our contribution guidelines below.

## How to Contribute

The preferred workflow to contribute to mantra is as follows:

1. Fork the [GitHub repository](http://www.github.com/RJT1990/mantra) by clicking the **Fork** button in the top-right of the page. This will produce a copy of the repository in your GitHub account.

2. Clone your forked repository to your local machine:
    ```bash
    $ git clone https://github.com/YourUsername/mantra.git
    $ cd mantra
    ```

3. Create a branch to hold your changes - such as a bug fix, a new feature or enhancement:
     ```bash
    $ git checkout -b new-feature
    ```

4. Develop your branch. Add new or modified files, and commit with an informative message:
     ```bash
    $ git add modified_files
    $ git commit -m "Fix typo in getting started docs"
    ```
    Changes can be pushed to GitHub as follows:
     ```bash
    $ git push -u origin new-feature
    ```
    
5. When you are happy, you can create a pull request from your fork. [See here for instructions on how to do this](https://help.github.com/articles/creating-a-pull-request-from-a-fork).

For more help on using Git, you can view the [Git documentation](https://git-scm.com/documentation). More generally, if you get stuck, just ask one of our developers on our [Gitter channel](https://gitter.im/mantraml/Lobby) (or other mediums): we'd be happy to help! 

## Pull Request Checklist

Before submitting a pull request, make sure you go over the following checklist:

- **Check the Coding Guidelines**: available in this document [here](https://github.com/RJT1990/mantra/blob/master/CONTRIBUTING.md#coding-guidelines)
- **Ensure you have a helpful PR title**: it should describe the bug fix, the feature enhancement, the documentation improvement, etc in a concise but informative way.
- **Link to issues you are resolving**: you may need to refer to multiple issues if your PR solves many.
- **Use informative docstrings**: public methods should have informative docstrings explaining the method arguments, the method output, as well as an example of the method being used (if appropriate).
- **Write tests for new features or bug fixes** - that verify that the intended behaviour is achieved.
- **Ensure you have good unit test coverage** - if your bug fix or enhancement involves new code, then you should ensure the tests you write have good coverage.
- **Ensure all tests pass** - if your PR leads to breaking changes elsewhere, then it will not be accepted, so ensure that all tests pass on your local.

## Filing Bugs and Feature Requests

Bugs and feature requests are filed using [GitHub Issues](https://github.com/RJT1990/mantra/issues). We welcome your bug reports and your ideas for new features.

Please note when reporting bugs:

- Check existing issues and ensure the bug hasn't been reported before.
- Include a code snippet so others can replicate the problem.
- Include your Python version and mantra version.
- Describe the expected and actual behaviour, and how they differ.

Use the **bug** issue tag for bug reports. Use the **enhancement** issue tag for new feature requests. If your issue is something that would be good for a first-time contributor to solve - it does not require intimate knowledge of the codebase - then also flag with a **good first issue** tag.

## Tips for New Contributors

It's always a little awkward contributing to an existing project for the first time - even more so, if it's your first ever open source contribution. We have a couple of tips:

- Look out for **good first issue** tags: [view the list of current good first issues here](https://github.com/RJT1990/mantra/labels/good%20first%20issue). These issues are good for first time contributors because they are usually isolated problems. Core developers will appreciate your work as it means they can focus on other issues.

- **Don't worry about making mistakes** : your act of contribution far outweighs any mistakes you'll make when first contributing to a project.

- **Ask for advice**: We have a [Gitter channel](https://gitter.im/mantraml/Lobby) where you can talk to other developers, and ask for advice about how/where to contribute.

- **It's not just about code** : documentation is incredibly important, for example. Any contribution you make to improve the docs will be greatly appreciated. Many open source developers starts their contributions in docs before moving to the codebase.

- **Have fun and learn!** - open source is a great way to advance your programming ability by working and learning aside others on cool problems. And don't overdo things: take breaks when you need to.

## Working with the Docs

To build the docs, you will need to install [Sphinx](http://www.sphinx-doc.org/en/master/). To build the docs:

 ```bash
$ cd mantraml/docs
$ sphinx-build source build
```

This will build the docs inside the `docs/` folder. The source files are located within the `source/` folder. The workflow to follow is to edit the `.rst` files within the `source/` folder, run the build command above, and then check the build files to check the output.

If you are submitting a change to the docs as part of a pull request, then use the **documentation** tag.

## Working with  Tests

To run the tests, first install pytest:

 ```bash
pip install pytest pytest-cov
```

To run the tests on the project:

 ```bash
$ cd mantraml
$ pytest mantraml
```

To check the coverage of the tests, from the same directory:

 ```bash
pytest mantraml --cov mantraml
```

## Coding Guidelines

- Adhere to [PEP8](https://www.python.org/dev/peps/pep-0008/) style guidelines.
- Never use `import *`!
- Public methods should have docstrings, and if appropriate, example method use cases.

To check PEP8 compliance you can use the flake8 library:

 ```bash
pip install flake8
cd mantraml
flake8 mantraml
```

We are generally quite permissive about exceeding the PEP8 line character limit (79) but we would advise you to only exceed it if there is a good reason, otherwise it's a strong refactoring signal.



