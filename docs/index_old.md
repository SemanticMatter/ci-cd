# GitHub Action reusable workflows

This repository contains reusable workflows for GitHub Actions.

They are mainly for usage with modern Python package repositories.

## Available workflows

The callable, reusable workflows available from this repository are described in detail in this documentation under the "Workflows" section.

## General usage

See the [GitHub Docs](https://docs.github.com/en/actions/using-workflows/reusing-workflows#calling-a-reusable-workflow) on the topic of calling a reusable workflow to understand how one can incoporate one of these workflows in your workflow.

!!! note
    Workflow-level set `env` context variables cannot be used when setting input values for the called workflow.
    See the [GitHub documentation](https://docs.github.com/en/actions/learn-github-actions/contexts#env-context) for more information on the `env` context.

Under the "Workflows" section for each available workflow, a usage example will be given.

## License & copyright

This repository licensed under the  [MIT LICENSE](LICENSE.md) with copyright &copy; 2022 Casper Welzel Andersen ([CasperWA](https://github.com/CasperWA)).
