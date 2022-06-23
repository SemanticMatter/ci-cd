# GitHub Action reusable workflows

This repository contains reusable workflows for GitHub Actions.

They are mainly for usage with modern Python package repositories.

Available workflows:

- [CD - Release](#cd---release-cd_releaseyml)

## Usage

See the [GitHub Docs](https://docs.github.com/en/actions/using-workflows/reusing-workflows#calling-a-reusable-workflow) on the topic of calling a reusable workflow to understand how one can incoporate one of these workflows in your workflow.

Example (using [CD - Release](#cd---release-cd_releaseyml)):

```yaml
name: CD - Publish

on:
  release:
    types:
    - published

env:
  PUBLISH_UPDATE_BRANCH: stable
  GIT_USER_NAME: "Casper W. Andersen"
  GIT_USER_EMAIL: "CasperWA@github.com"

jobs:
  publish:
    name: Publish package and documentation
    uses: CasperWA/gh-actions/.github/workflows/cd_release.yml@main
    if: github.repository == 'CasperWA/my-py-package' && startsWith(github.ref, 'refs/tags/v')
    with:
      git_username: ${{ env.GIT_USER_NAME }}
      git_email: ${{ env.GIT_USER_EMAIL }}
      release_branch: ${{ env.PUBLISH_UPDATE_BRANCH }}
      install_extras: "[dev,build]"
      doc_extras: "[docs]"
      update_docs: true
      build_cmd: "flit build"
    secrets:
      PyPI_token: ${{ secrets.PYPI_TOKEN }}
      release_PAT: ${{ secrets.PAT }}
```

## CD - Release (`cd_release.yml`)

There are 2 jobs in this workflow, which run in sequence.

First, an update & publish job, which updates the version in the package's root `__init__.py` file through an [Invoke](https://pyinvoke.org) task.
The newly created tag (created due to the caller workflow running `on.release.types.published`) will be updated accordingly, as will the publish branch (defaults to `main`).

Secondly, a job to update the documentation is run, however, this can be deactivated.
The job expects the documentation to be setup with the [mike](https://github.com/jimporter/mike)+[MkDocs](https://www.mkdocs.org)+[GitHub Pages](https://pages.github.com/) framework.

### Expectations

This workflow should _only_ be used for releasing a single modern Python package.

The repository contains the following:

- (**required**) A root `tasks.py` file with invoke tasks, one being `setver`, which accepts a `--version` option.
- (optional) A release tag message text file located at `.github/utils/release_tag_msg.txt`.

### Inputs

| **Name** | **Descriptions** | **Required** | **Default** | **Type** |
|:--- |:--- |:---:|:---:|:---:|
| git_username | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| git_email | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| release_branch | The branch name to release/publish from. | No | main | _string_ |
| install_extras | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[dev,release]'`. | No | _Empty string_ | _string_ |
| python_version | The Python version to use for the workflow. | No | 3.9 | _string_ |
| update_docs | Whether or not to also run the 'docs' workflow job. | No | `false` | _boolean_ |
| doc_extras | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Note, if this is empty, 'install_extras' will be used as a fallback.</br></br>Example: `'[docs]'`. | No | _Empty string_ | _string_ |
| build_cmd | The package build command, e.g., 'flit build' or 'python -m build' (default). | No | `python -m build` | _string_ |

### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| PyPI_token | A PyPI token for publishing the built package to PyPI. | **_Yes_** |
| release_PAT | A personal access token (PAT) with rights to update the 'release_branch'. This will fallback on `GITHUB_TOKEN`. | No |
