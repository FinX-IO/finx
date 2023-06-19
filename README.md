# BUILD STATUS

### CircleCI

#### main branch: [![CircleCI](https://dl.circleci.com/status-badge/img/gh/FinX-IO/finx/tree/main.svg?style=svg&circle-token=0)](https://dl.circleci.com/status-badge/redirect/gh/FinX-IO/finx/tree/main)

#### dev branch: [![CircleCI](https://dl.circleci.com/status-badge/img/gh/FinX-IO/finx/tree/dev.svg?style=svg&circle-token=0)](https://dl.circleci.com/status-badge/redirect/gh/FinX-IO/finx/tree/dev)

### FinX Capital Markets LLC

Please see LICENSE and SECURITY for terms of use.

***

# FinX Python Software Development Kit

The **FinX SDK** is a python package that has interfaces to the FinX Capital Markets
Analytics Platform (the 'FinX Platform'). The code in the SDK makes calls to REST APIs 
& WebSocket endpoints. A valid ___FinX API Key___ is required for the SDK to return results.

To obtain an API Key, please contact us FinX Capital Markets LLC [via email](mailto:info@finx.io).

***

# Installation

## Requirements

The FinX SDK requires Python 3.10 or higher.

### ENVIRONMENT VARIABLES

The FinX SDK will look for the following environment variables that are provided by FinX Capital Markets. You may find these
in your user account settings, or in the email sent to you upon registration. 

1. `FINX_API_KEY` - The API Key provided by FinX Capital Markets LLC
2. `FINX_API_URL` - The URL of the FinX Platform API.
3. `FINX_API_URL_BACKUP` - The backup URL of the FinX Platform API.
4. `FINX_USER_EMAIL` - The email address used to register with FinX.

If building the SDK to test-pypi or to pypi, the following environment variables are required:

1. `TWINE_USERNAME` - The username for the pypi account.
2. `TWINE_PASSWORD` - The password for the pypi account.

---
title: FinX Python SDK
tags: technology, documentation, python
---
