This python package is the **FinX Python SDK** and is used to interface with the **FinX Capital Markets Analytics 
Platform**.


| Branch | Build & Test Results                                                                                                                                                                                                          |
| ------ |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PyPi.org | [![CircleCI](https://dl.circleci.com/status-badge/img/gh/FinX-IO/finx/tree/main.svg?style=svg&circle-token=a2c782bbf496cf79a9dbee9a41960601a56d28f7)](https://dl.circleci.com/status-badge/redirect/gh/FinX-IO/finx/tree/main) |
| Test.PyPi.org | [![CircleCI](https://dl.circleci.com/status-badge/img/gh/FinX-IO/finx/tree/dev.svg?style=svg&circle-token=a2c782bbf496cf79a9dbee9a41960601a56d28f7)](https://dl.circleci.com/status-badge/redirect/gh/FinX-IO/finx/tree/dev)   |

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

### Python Packages

In your container, pipenv or other python environment, you must have the following
packages installed:

```requirements.txt
aiohttp>=3.8.4
setuptools>=67.0.0
nest-asyncio>=1.5.6
numpy>=1.25.0
pandas>=2.0.2
plotly>=5.15.0
pytest>=6.2.5
requests>=2.31.0
scipy>=1.10.1
websocket-client>=1.6.0
websockets>=11.0.3
```

### ENVIRONMENT VARIABLES

The FinX SDK will look for the following environment variables that are provided by FinX Capital Markets. You may find these
in your user account settings, or in the email sent to you upon registration. 

1. `FINX_API_KEY` - The API Key provided by FinX Capital Markets LLC
2. `FINX_API_URL` - The URL of the FinX Platform API.
3. `FINX_USER_EMAIL` - The email address used to register with FinX.

## Install from PyPI using Pip

In your python environment of choice, install finx using Pip:

    #! /bin/bash
    pip install finx-io --upgrade
    
### Pipenv installation

Pipenv is a handy tool for managing python environments. To install finx using pipenv, run the following commands:

    #! /bin/bash
    pipenv clean
    pipenv install aiohttp setuptools nest-asyncio numpy pandas plotly pytest requests scipy websocket-client websockets
    pipenv install finx-io 

## Check Installation and Environment Variables with Pipenv

Here's a full example of how to install finx using pipenv, with a quick test to ensure the environment variables are set correctly:

    #! /bin/bash
    pipenv clean
    pipenv install aiohttp setuptools nest-asyncio numpy pandas plotly pytest requests scipy websocket-client websockets
    pipenv install finx-io 
    pipenv shell
    export FINX_API_KEY=<your-api-key>
    export FINX_API_URL=<your-api-url>
    export FINX_USER_EMAIL=<your-email>
    python3 -c "import finx; from finx.client import FinXClient; finx_client = FinXClient('socket', ssl=True); function_list = finx_client.list_api_functions(); print(function_list)"

## Python Shell

You can set or fetch environment variables locally in python if you wish:
```python3
#! /usr/bin/env python3
import os
import finx
from finx.client import FinXClient

finx_client = FinXClient(
    'socket', 
    ssl=True, 
    FINX_API_KEY = os.getenv('FINX_API_KEY'), 
    FINX_API_URL = os.getenv('FINX_API_URL'), 
    FINX_USER_EMAIL = os.getenv('FINX_USER_EMAIL'))
function_list = finx_client.list_api_functions()
print(function_list)
```
Full **Documentation** with all available functions is available at [FinX Docs](https://finx-capital-markets.gitbook.io/)

---
title: FinX Python SDK
tags: technology, documentation, python
---
