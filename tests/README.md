This is where the functional and integration tests are for mantraml. They test the behaviour of the library as the user would use it.

Note this is different from `mantraml/tests` which are unit tests run within the library, to make sure the library is internally consistent.

Directories:

- `0build/` - where the mantraml package is built and installed. This should always be run first, so it has `0` at the beginning.
- `functional/` - various functional tests that are automatically run on CircleCI
- `local/` - complex, long-running tests that should be only used on local machines, e.g. provisioning AWS machines, remote training, etc..

# Local testing docs

IMPORTANT: all scripts use the package version in PyPI, and not the local version. To get consistent results make sure the version is the same locally and on PyPI.

## `local/test_training_aws.sh`

This scripts assumes you have a test project in the `test_training_aws` subdirectory of `local`, and AWS integration has been set up locally.

The test projects should have the `decks` dataset and the `my_first_model` model.
