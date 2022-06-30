# GitHub Action reusable workflows

This repository contains reusable workflows for GitHub Actions.

They are mainly for usage with modern Python package repositories.

Available workflows:

- [CD - Release](#cd---release-cd_releaseyml)
- [CI - Check dependencies](#ci---check-dependencies-ci_check_pyproject_dependenciesyml)

## Usage

See the [GitHub Docs](https://docs.github.com/en/actions/using-workflows/reusing-workflows#calling-a-reusable-workflow) on the topic of calling a reusable workflow to understand how one can incoporate one of these workflows in your workflow.

> **Note**: Workflow-level set `env` context variables cannot be used when setting input values for the called workflow.
> See the [GitHub documentation](https://docs.github.com/en/actions/learn-github-actions/contexts#env-context) for more information on the `env` context.

Example (using [CD - Release](#cd---release-cd_releaseyml)):

```yaml
name: CD - Publish

on:
  release:
    types:
    - published

jobs:
  publish:
    name: Publish package and documentation
    uses: CasperWA/gh-actions/.github/workflows/cd_release.yml@main
    if: github.repository == 'CasperWA/my-py-package' && startsWith(github.ref, 'refs/tags/v')
    with:
      git_username: "Casper Welzel Andersen"
      git_email: "CasperWA@github.com"
      release_branch: stable
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
| `git_username` | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| `git_email` | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| `release_branch` | The branch name to release/publish from. | No | main | _string_ |
| install_extras | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[dev,release]'`. | No | _Empty string_ | _string_ |
| `python_version` | The Python version to use for the workflow. | No | 3.9 | _string_ |
| `update_docs` | Whether or not to also run the 'docs' workflow job. | No | `false` | _boolean_ |
| `doc_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Note, if this is empty, 'install_extras' will be used as a fallback.</br></br>Example: `'[docs]'`. | No | _Empty string_ | _string_ |
| `build_cmd` | The package build command, e.g., `'flit build'` or `'python -m build'` (default). | No | `python -m build` | _string_ |

### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `PyPI_token` | A PyPI token for publishing the built package to PyPI. | **_Yes_** |
| `release_PAT` | A personal access token (PAT) with rights to update the `release_branch`. This will fallback on `GITHUB_TOKEN`. | No |

## CI - Check dependencies (`ci_check_pyproject_dependencies.yml`)

This workflow runs an [Invoke](https://pyinvoke.org) task to check dependencies in a `pyproject.toml` file.

The reason for having this workflow and not using [Dependabot](https://github.com/dependabot/dependabot-core) is because it seems to not function properly with this use case.

> **Warning**: If a PAT is not passed through for the `release_PAT` secret and `GITHUB_TOKEN` is used, beware that any other CI/CD jobs that run for, e.g., pull request events, may not run since `GITHUB_TOKEN`-generated PRs are designed to not start more workflows to avoid escalation.
> Hence, if it is important to run CI/CD workflows for pull requests, consider passing a PAT as a secret to this workflow represented by the `release_PAT` secret.

<!-- markdownlint-disable-next-line MD024 -->
### Expectations

The repository contains the following:

- (**required**) A root `tasks.py` file with invoke task `update-deps`.
- (optional) A PR body text file, the path to which can be specified in the `pr_body_file` input.

<!-- markdownlint-disable-next-line MD024 -->
### Inputs

| **Name** | **Descriptions** | **Required** | **Default** | **Type** |
|:--- |:--- |:---:|:---:|:---:|
| `git_username` | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| `git_email` | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| `permanent_dependenices_branch` | The branch name for the permanent dependency updates branch. | No | ci/dependency-updates | _string_ |
| `python_version` | The Python version to use for the workflow. | No | 3.9 | _string_ |
| `install_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[dev,release]'`. | No | _Empty string_ | _string_ |
| `pr_body_file` | Relative path to PR body file from the root of the repository.</br></br>Example: `'.github/utils/pr_body_deps_check.txt'`. | No | _Empty string_ | _string_ |

<!-- markdownlint-disable-next-line MD024 -->
### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `release_PAT` | A personal access token (PAT) with rights to update the `permanent_dependencies_branch`. This will fallback on `GITHUB_TOKEN`. | No |
