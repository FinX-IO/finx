# BUILD STATUS

### CircleCI

#### main branch: [![CircleCI](https://dl.circleci.com/status-badge/img/gh/FinX-IO/finx/tree/main.svg?style=svg&circle-token=a2c782bbf496cf79a9dbee9a41960601a56d28f7)](https://dl.circleci.com/status-badge/redirect/gh/FinX-IO/finx/tree/main)

#### dev branch: [![CircleCI](https://dl.circleci.com/status-badge/img/gh/FinX-IO/finx/tree/dev.svg?style=svg&circle-token=a2c782bbf496cf79a9dbee9a41960601a56d28f7)](https://dl.circleci.com/status-badge/redirect/gh/FinX-IO/finx/tree/dev)

### FinX Capital Markets LLC

Please see LICENSE and SECURITY for terms of use.

***

# FinX Python Software Development Kit

The **FinX SDK** is a python package that has interfaces to the FinX Capital Markets
Analytics Platform (the 'FinX Platform'). The code in the SDK makes calls to REST APIs 
& WebSocket endpoints. A valid ___FinX API Key___ is required for the SDK to return results.

To obtain an API Key, please visit [https://app.finx.io](https://app.finx.io) and register for an account.

Full **Documentation** is available at [http://docs.finx.io](http://docs.finx.io)

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

## Install from PyPI using Pip

In your python environment of choice, install finx using Pip:

    #! /bin/bash
    pip install finx
    

## Check Installation and Environment Variables with Pipenv

    #! /bin/bash
    pipenv install finx
    pipenv shell
    export FINX_API_KEY=<your-api-key>
    export FINX_API_URL=<your-api-url>
    export FINX_API_URL_BACKUP=<your-api-url-backup>
    export FINX_USER_EMAIL=<your-email>
    python3 -c "import finx; from finx import version; print(version.VERSION)"
    python3 -c "import finx; from finx.client import FinXClient; finx_client = FinXClient('socket', ssl=True); function_list = finx_client.list_api_functions(); print(function_list)"

## Quick Start Example

Here's a quick python snippet to get you started:

```python3
#! /usr/bin/env python3
import os
import finx
from finx.client import FinXClient
os.environ('FINX_API_KEY') = '<your-api-key>'
os.environ('FINX_API_URL') = '<your-api-url>'
os.environ('FINX_API_URL_BACKUP') = '<your-api-url-backup>'
os.environ('FINX_USER_EMAIL') = '<your-email>'

finx_client = FinXClient('socket', ssl=True)
function_list = finx_client.list_api_functions()
print(function_list)
```

---
title: FinX Python SDK
tags: technology, documentation, python
---
