# sync-files-across-repos

<!-- Space: devwithkrishna -->
<!-- Parent: GitHub -->

<!-- Macro: :toc:
     Template: ac:toc
     Printable: 'false'
     MinLevel: 2 
-->
     
<!-- Include: docs/warning.tpl -->

:toc:

A Python utility for syncing files across multiple repositories. This tool enables you to maintain consistency of shared files across multiple git repositories.

## Overview

`sync-files-across-repos` automates the process of synchronizing specific files from a source repository to multiple target repositories. Perfect for maintaining consistent configuration files, documentation, or shared assets across related projects.

## Features

- 🔄 Sync files across multiple repositories
- 📝 Configuration-based file mapping
- 🔍 Logging for tracking sync operations
- ⚙️ Easy setup and configuration
- 🐍 Built with Python

<!-- action-docs-all source="action.yml" project="devwithkrishna/sync-files-across-repos" version="v1.0.0" -->
## Description

Composite action to sync files across multiple repositories. This tool enables you to maintain consistency of shared files across multiple git repositories


## Inputs

| name | description | required | default |
| --- | --- | --- | --- |
| `organization` | <p>GitHub organization name</p> | `true` | `""` |
| `prefix` | <p>GitHub repository name prefix to filter repositories (optional)</p> | `false` | `""` |
| `path` | <p>Path to the file to replicate</p> | `true` | `""` |
| `file` | <p>Name of the file to sync</p> | `true` | `""` |


## Runs

This action is a `composite` action.

## Usage

```yaml
- uses: devwithkrishna/sync-files-across-repos@v1.1.0
  with:
    organization:
    # GitHub organization name
    #
    # Required: true
    # Default: ""

    prefix:
    # GitHub repository name prefix to filter repositories (optional)
    #
    # Required: false
    # Default: ""

    path:
    # Path to the file to replicate
    #
    # Required: true
    # Default: ""

    file:
    # Name of the file to sync
    #
    # Required: true
    # Default: ""
```
<!-- action-docs-all source="action.yml" project="devwithkrishna/sync-files-across-repos" version="v1.0.0" -->

## Project Structure

```
sync-files-across-repos/
├── sync_file.py           # Main sync script
├── setup_logging.py       # Logging configuration
├── logging-conf.yaml      # Logging config
├── pyproject.toml         # Project metadata
├── Makefile               # Build automation
├── uv.lock                # Dependency lock file
└── README.md              # This file
```

<!-- Include: docs/footer.tpl -->
