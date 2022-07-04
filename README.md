# GitHub Action reusable workflows

This repository contains reusable workflows for GitHub Actions.

They are mainly for usage with modern Python package repositories.

Available workflows:

- [CD - Release](#cd---release-cd_releaseyml)
- [CI - Activate auto-merging for PRs](#ci---activate-auto-merging-for-prs-ci_automerge_prsyml)
- [CI - Check dependencies](#ci---check-dependencies-ci_check_pyproject_dependenciesyml)
- [CI - Update dependencies](#ci---update-dependencies-ci_update_dependenciesyml)
- [CI/CD - New updates to default branch](#cicd---new-updates-to-default-branch-ci_cd_updated_default_branchyml)

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
      tag_message_file: ".github/utils/release_tag_msg.txt"
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

- (**required**) A Python package root `__init__.py` file with `__version__` defined.
- (**required**) The workflow is run for a tag that starts with `v` followed by a full semantic version.
  This will automatically be the case for a GitHub release, which creates a new tag that starts with `v`.
  See [SemVer.org](https://semver.org) for more information about semantic versioning.

### Inputs

| **Name** | **Descriptions** | **Required** | **Default** | **Type** |
|:--- |:--- |:---:|:---:|:---:|
| `package_dir` | Path to the Python package directory relative to the repository directory.</br></br>Example: `'src/my_package'`. | **_Yes_** | | _string_ |
| `git_username` | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| `git_email` | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| `release_branch` | The branch name to release/publish from. | No | main | _string_ |
| `install_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[dev,release]'`. | No | _Empty string_ | _string_ |
| `python_version` | The Python version to use for the workflow. | No | 3.9 | _string_ |
| `update_docs` | Whether or not to also run the 'docs' workflow job. | No | `false` | _boolean_ |
| `doc_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Note, if this is empty, 'install_extras' will be used as a fallback.</br></br>Example: `'[docs]'`. | No | _Empty string_ | _string_ |
| `build_cmd` | The package build command, e.g., `'flit build'` or `'python -m build'` (default). | No | `python -m build` | _string_ |
| `tag_message_file` | Relative path to a release tag message file from the root of the repository.</br></br>Example: `'.github/utils/release_tag_msg.txt'`. | No | _Empty string_ | _string_ |
| `test` | Whether to use the TestPyPI repository index instead of PyPI. | No | `false` | _boolean_ |

### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `PyPI_token` | A PyPI token for publishing the built package to PyPI. | **_Yes_** |
| `release_PAT` | A personal access token (PAT) with rights to update the `release_branch`. This will fallback on `GITHUB_TOKEN`. | No |

## CI - Activate auto-merging for PRs (`ci_automerge_prs.yml`)

Activate auto-merging for a PR.

<!-- markdownlint-disable-next-line MD024 -->
### Expectations

The `release_PAT` secret must represent a user with the rights to activate auto-merging.

This workflow can _only_ be called if the triggering event from the caller workflow is `pull_request_target`.

<!-- markdownlint-disable-next-line MD024 -->
### Inputs

There are no inputs for this workflow.

<!-- markdownlint-disable-next-line MD024 -->
### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `release_PAT` | A personal access token (PAT) with rights to update the `permanent_dependencies_branch`. This will fallback on `GITHUB_TOKEN`. | No |

## CI - Check dependencies (`ci_check_pyproject_dependencies.yml`)

This workflow runs an [Invoke](https://pyinvoke.org) task to check dependencies in a `pyproject.toml` file.

The reason for having this workflow and not using [Dependabot](https://github.com/dependabot/dependabot-core) is because it seems to not function properly with this use case.

> **Warning**: If a PAT is not passed through for the `release_PAT` secret and `GITHUB_TOKEN` is used, beware that any other CI/CD jobs that run for, e.g., pull request events, may not run since `GITHUB_TOKEN`-generated PRs are designed to not start more workflows to avoid escalation.
> Hence, if it is important to run CI/CD workflows for pull requests, consider passing a PAT as a secret to this workflow represented by the `release_PAT` secret.

<!-- markdownlint-disable-next-line MD024 -->
### Expectations

The repository contains the following:

- (**required**) A repository root `pyproject.toml` file with the Python package's dependencies.

<!-- markdownlint-disable-next-line MD024 -->
### Inputs

| **Name** | **Descriptions** | **Required** | **Default** | **Type** |
|:--- |:--- |:---:|:---:|:---:|
| `git_username` | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| `git_email` | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| `permanent_dependencies_branch` | The branch name for the permanent dependency updates branch. | No | ci/dependency-updates | _string_ |
| `python_version` | The Python version to use for the workflow. | No | 3.9 | _string_ |
| `install_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[dev,release]'`. | No | _Empty string_ | _string_ |
| `pr_body_file` | Relative path to PR body file from the root of the repository.</br></br>Example: `'.github/utils/pr_body_deps_check.txt'`. | No | _Empty string_ | _string_ |
| `fail_fast` | Whether the task to update dependencies should fail if any error occurs. | No | `false` | _boolean_ |
| `pr_labels` | A comma separated list of strings of GitHub labels to use for the created PR. | No | _Empty string_ | _string_ |

<!-- markdownlint-disable-next-line MD024 -->
### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `release_PAT` | A personal access token (PAT) with rights to update the `permanent_dependencies_branch`. This will fallback on `GITHUB_TOKEN`. | No |

## CI - Update dependencies (`ci_update_dependencies.yml`)

This workflow creates a PR if there are any updates in the `permanent_dependencies_branch` branch that have not been included in the `default_repo_branch` branch.

This workflow works nicely together with the [CI - Check dependencies](#ci---check-dependencies-ci_check_pyproject_dependenciesyml) workflow, and the same value for `permanent_dependencies_branch` should be used.
In this way, this workflow can be called on a schedule to update the dependencies that have been merged into the `permanent_dependencies_branch` branch into the `default_repo_branch` branch.

The main point of having this workflow is to have a single PR, which can be squash merged, to merge several dependency updates performed by [Dependabot](https://github.com/dependabot/dependabot-core) or similar.

As a "bonus" this workflow supports updating [pre-commit](https://pre-commit.com) hooks.

> **Warning**: If a PAT is not passed through for the `release_PAT` secret and `GITHUB_TOKEN` is used, beware that any other CI/CD jobs that run for, e.g., pull request events, may not run since `GITHUB_TOKEN`-generated PRs are designed to not start more workflows to avoid escalation.
> Hence, if it is important to run CI/CD workflows for pull requests, consider passing a PAT as a secret to this workflow represented by the `release_PAT` secret.
<!-- markdownlint-disable-next-line MD028 -->

> **Important**: If this is to be used together with the [CI/CD - New updates to default branch](#cicd---new-updates-to-default-branch-ci_cd_updated_default_branchyml) workflow, the `pr_body_file` supplied (if any) should be immutable within the first 8 lines, i.e., no check boxes or similar in the first 8 lines.
> Indeed, it is recommended to not supply a `pr_body_file` in this case.

<!-- markdownlint-disable-next-line MD024 -->
### Expectations

There are no expectations of the repo when using this workflow.

<!-- markdownlint-disable-next-line MD024 -->
### Inputs

| **Name** | **Descriptions** | **Required** | **Default** | **Type** |
|:--- |:--- |:---:|:---:|:---:|
| `git_username` | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| `git_email` | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| `permanent_dependencies_branch` | The branch name for the permanent dependency updates branch. | No | ci/dependency-updates | _string_ |
| `default_repo_branch` | The branch name of the repository's default branch. More specifically, the branch the PR should target. | No | main | _string_ |
| `pr_body_file` | Relative path to PR body file from the root of the repository.</br></br>Example: `'.github/utils/pr_body_update_deps.txt'`. | No | _Empty string_ | _string_ |
| `pr_labels` | A comma separated list of strings of GitHub labels to use for the created PR. | No | _Empty string_ | _string_ |
<!-- markdownlint-disable-next-line MD038 -->
| `extra_to_dos` | A multi-line string (insert `\n` to create line breaks) with extra 'to do' checks. Should start with `- [ ] `. | No | _Empty string_ | _string_ |
| `update_pre-commit` | Whether or not to update pre-commit hooks as part of creating the PR. | No | `false` | _boolean_ |
| `python_version` | The Python version to use for the workflow.</br></br>**Note**: This is only relevant if `update_pre-commit` is `true`. | No | 3.9 | _string_ |
| `install_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[dev,pre-commit]'`.</br></br>**Note**: This is only relevant if `update_pre-commit` is `true`. | No | _Empty string_ | _string_ |
| `skip_pre-commit_hooks` | A comma-separated list of pre-commit hook IDs to skip when running `pre-commit` after updating hooks.</br></br>**Note**: This is only relevant if `update_pre-commit` is `true`. | No | _Empty string_ | _string_ |

<!-- markdownlint-disable-next-line MD024 -->
### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `release_PAT` | A personal access token (PAT) with rights to update the `permanent_dependencies_branch`. This will fallback on `GITHUB_TOKEN`. | No |

## CI/CD - New updates to default branch (`ci_cd_updated_default_branch.yml`)

Keep your `permanent_dependencies_branch` branch up-to-date with changes in your main development branch, i.e., the `default_repo_branch`.

Furthermore, this workflow can optionally update the `latest` [mike](https://github.com/jimporter/mike)+[MkDocs](https://www.mkdocs.org)+[GitHub Pages](https://pages.github.com/)-framework documentation release alias, which represents the `default_repo_branch`.

> **Warning**: If a PAT is not passed through for the `release_PAT` secret and `GITHUB_TOKEN` is used, beware that any other CI/CD jobs that run for, e.g., pull request events, may not run since `GITHUB_TOKEN`-generated PRs are designed to not start more workflows to avoid escalation.
> Hence, if it is important to run CI/CD workflows for pull requests, consider passing a PAT as a secret to this workflow represented by the `release_PAT` secret.
<!-- markdownlint-disable-next-line MD028 -->

> **Important**: If this is to be used together with the [CI - Update dependencies](#ci---update-dependencies-ci_update_dependenciesyml) workflow, the `pr_body_file` supplied to that workflow (if any) should match the `update_depednencies_pr_body_file` input in this workflow and be immutable within the first 8 lines, i.e., no check boxes or similar in the first 8 lines.
> Indeed, it is recommended to not supply `pr_body_file` to the [CI - Update dependencies](#ci---update-dependencies-ci_update_dependenciesyml) workflow as well as to not supply the `update_dependencies_pr_body_file` in this workflow in this case.

<!-- markdownlint-disable-next-line MD024 -->
### Expectations

The repository contains the following:

- (**required**) A single Python package is contained in the `package_dir` directory.
- (**required**) _Only if also updating the documentation_, then the documentation should be contained in a root `docs` directory.
- (**required**) _Only if also updating the documentation_, then a root `README.md` file must exist and desired to be used as the documentation's landing page if the `update_docs_landing_page` is set to `true`, which is the default.

<!-- markdownlint-disable-next-line MD024 -->
### Inputs

| **Name** | **Descriptions** | **Required** | **Default** | **Type** |
|:--- |:--- |:---:|:---:|:---:|
| `package_dir` | Path to the Python package directory relative to the repository directory.</br></br>Example: `'src/my_package'`. | **_Yes_** | | _string_ |
| `git_username` | A git username (used to set the 'user.name' config option). | **_Yes_** | | _string_ |
| `git_email` | A git user's email address (used to set the 'user.email' config option). | **_Yes_** | | _string_ |
| `permanent_dependencies_branch` | The branch name for the permanent dependency updates branch. | No | ci/dependency-updates | _string_ |
| `default_repo_branch` | The branch name of the repository's default branch. More specifically, the branch the PR should target. | No | main | _string_ |
| `update_dependencies_pr_body_file` | Relative path to a PR body file from the root of the repository, which is used in the 'CI - Update dependencies' workflow, if used.</br></br>Example: `'.github/utils/pr_body_update_deps.txt'`. | No | _Empty string_ | _string_ |
| `update_docs` | Whether or not to also run the 'docs' workflow job. | No | `false` | _boolean_ |
| `update_docs_landing_page` | Whether or not to update the documentation landing page. The landing page will be based on the root README.md file. | No | `true` | _boolean_ |
| `python_version` | The Python version to use for the workflow.</br></br>**Note**: This is only relevant if `update_pre-commit` is `true`. | No | 3.9 | _string_ |
| `doc_extras` | Any extras to install from the local repository through 'pip'. Must be encapsulated in square parentheses (`[]`) and be separated by commas (`,`) without any spaces.</br></br>Example: `'[docs]'`. | No | _Empty string_ | _string_ |
| `exclude_dirs` | Comma-separated list of directories to exclude in the Python API reference documentation. Note, only directory names, not paths, may be included. Note, all folders and their contents with these names will be excluded. Defaults to `'__pycache__'`. **Important**: When a user value is set, the preset value is overwritten - hence `'__pycache__'` should be included in the user value if one wants to exclude these directories. | No | \_\_pycache\_\_ | _string_ |
| `exclude_files` | Comma-separated list of files to exclude in the Python API reference documentation. Note, only full file names, not paths, may be included, i.e., filename + file extension. Note, all files with these names will be excluded. Defaults to `'__init__.py'`. **Important**: When a user value is set, the preset value is overwritten - hence `'__init__.py'` should be included in the user value if one wants to exclude these files. | No | \_\_init\_\_.py | _string_ |
| `full_docs_dirs` | Comma-separated list of directories in which to include everything - even those without documentation strings. This may be useful for a module full of data models or to ensure all class attributes are listed. | No | _Empty string_ | _string_ |
| `landing_page_replacements` | List of replacements (mappings) to be performed on README.md when creating the documentation's landing page (index.md). This list _always_ includes replacing `'docs/'` with an empty string to correct relative links, i.e., this cannot be overwritten. By default `'(LICENSE)'` is replaced by `'(LICENSE.md)'`. | No | (LICENSE),(LICENSE.md) | _string_ |
| `landing_page_replacements_separator` | String to separate replacement mappings from the 'replacements' input. Defaults to a pipe (`\|`). | No | \| | _string_ |
| `landing_page_replacements_mapping_separator` | String to separate a single mapping's 'old' to 'new' statement. Defaults to a comma (`,`). | No | , | _string_ |

<!-- markdownlint-disable-next-line MD024 -->
### Secrets

| **Name** | **Descriptions** | **Required** |
|:--- |:--- |:---:|
| `release_PAT` | A personal access token (PAT) with rights to update the `permanent_dependencies_branch`. This will fallback on `GITHUB_TOKEN`. | No |
