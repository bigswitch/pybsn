# Contributing to this repository

### Ready to make a change? Fork the repo

Fork using GitHub Desktop:

- [Getting started with GitHub Desktop](https://docs.github.com/en/desktop/installing-and-configuring-github-desktop/getting-started-with-github-desktop) will guide you through setting up Desktop.
- Once Desktop is set up, you can use it to [fork the repo](https://docs.github.com/en/desktop/contributing-and-collaborating-using-github-desktop/cloning-and-forking-repositories-from-github-desktop)!

Fork using the command line:

- [Fork the repo](https://docs.github.com/en/github/getting-started-with-github/fork-a-repo#fork-an-example-repository) so that you can make your changes without affecting the original project until you're ready to merge them.

Fork with [GitHub Codespaces](https://github.com/features/codespaces):

- [Fork, edit, and preview](https://docs.github.com/en/free-pro-team@latest/github/developing-online-with-codespaces/creating-a-codespace) using [GitHub Codespaces](https://github.com/features/codespaces) without having to install and run the project locally.

### Make your update:
Make your changes to the file(s) you'd like to update. 
Test your changes by running all tests with `python -m unittest discover`.

### Open a pull request
When you're done making changes and you'd like to propose them for review, use the [pull request template](#pull-request-template) to open your PR (pull request).

### Submit your PR & get it reviewed
- Once you submit your PR, others from the pybsn community will review it with you.
- Automatic tests and code analysis will be run against your contribution. Make sure your code passes these checks. 
- After that, we may have questions, check back on your PR to keep up with the conversation.

### Your PR is merged!
Congratulations! The pybsn community thanks you. :sparkles:

### How to release a new version of pybsn
To help release a new version of pybsn, there are two github actions. They are triggered when a new tag is pushed to the repository. Each tag push is considered a release, and each of the two actions will attempt to create a release using the version found in [setup.py](https://github.com/bigswitch/pybsn/blob/main/setup.py). The name of the tag does not matter from a technical perspective, but should match the version in the `setup.py` file.
1. [release-github.yml](https://github.com/bigswitch/pybsn/blob/main/.github/workflows/release-github.yml)
Creates a release on github. The release description is the message of the last commit of the release branch (`main`).
2. [release-pypi.yml](https://github.com/bigswitch/pybsn/blob/main/.github/workflows/release-pypi.yml)
Creates a release on [PyPi](https://pypi.org/project/pybsn/).

### Attribution
This `CONTRIBUTING.md` has been adapted from [Github Docs](https://github.com/github/docs/blob/main/CONTRIBUTING.md).
