## FinX Capital Markets LLC

This python package is the **FinX Python SDK** and is used to interface with the **FinX Capital Markets Analytics 
Platform**.

Please see LICENSE and SECURITY for terms of use.
| Branch | Build & Test Results                                                                                                                                                                                                           |
| ------ |--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------|
| PyPi.org | INSERT BADGE |
| Test.PyPi.org | INSERT BADGE|
***

### FinX Python Software Development Kit

The **FinX SDK** is a python package that has interfaces to the FinX Capital Markets
Analytics Platform (the 'FinX Platform'). The code in the SDK makes calls to REST APIs 
& WebSocket endpoints. A valid ___FinX API Key___ is required for the SDK to return results.

To obtain an API Key, please visit [https://app.finx.io](https://app.finx.io) and register for an account.

Full **Documentation** is available at [https://finx-capital-markets.gitbook.io/](https://finx-capital-markets.gitbook.io/)

***

### Installation

### Requirements

The FinX SDK requires Python 3.10 or higher.

### Python Packages

In your container, pipenv or other python environment, you must have the following
packages installed:

```
aiohttp>=3.8.4
aenum>=3.1.15
asgiref>=3.8.1
setuptools>=67.0.0
nest-asyncio>=1.5.6
numpy>=1.25.0
pandas>=2.0.2
plotly>=5.15.0
pydantic>=2.3.0
pytest>=6.2.5
requests>=2.31.0
scipy>=1.10.1
websocket-client>=1.6.0
websockets>=11.0.3
pylint>=3.3.1
sphinx>=8.1.3
sphinx-autoapi>=3.3.3
autodoc_pydantic>=2.2.0
sphinx-rtd-theme>=3.0.2
```

### ENVIRONMENT VARIABLES

The FinX SDK will look for the following environment variables that are provided by FinX Capital Markets. You may find these
in your user account settings, or in the email sent to you upon registration. 

1. `FINX_API_KEY` - The API Key provided by FinX Capital Markets LLC
2. `FINX_API_URL` - The URL of the FinX Platform API.
3. `FINX_USER_EMAIL` - The email address used to register with FinX.

### Install from PyPI using Pip

In your python environment of choice, install finx using Pip:

    #! /bin/bash
    pip install finx-io --upgrade
    
### Pipenv installation

Pipenv is a handy tool for managing python environments. We recommend creating a fresh directory for running a clean 
pipenv environment. To install finx using pipenv, run the following commands:

    #! /bin/bash
    pipenv clean
    pipenv install aiohttp setuptools nest-asyncio numpy pandas plotly pytest requests scipy websocket websocket-client websockets
    pipenv install finx-io 

### Check Installation and Environment Variables with Pipenv

Here's a full example of how to install finx using pipenv, with a quick test to ensure the environment variables are set correctly:

    #! /bin/bash
    mkdir pipenv-temp && cd pipenv-temp
    pipenv clean
    pipenv install finx-io 
    pipenv shell
    export FINX_API_KEY=<replace-with-your-api-key>
    export FINX_API_URL=<replace-with-your-api-url>
    export FINX_USER_EMAIL=<replace-with-your-email>
    python3 -c "
        import finx
        from finx.client import ClientTypes, FinXClient
        finx_client = FinXClient(ClientTypes.socket)
        finx_client.load_functions()
        function_list = finx_client.list_api_functions()
        print(function_list)
        finx_client.cleanup()
    "

## Python Shell

Local Python3 Shell with environment variables pre-set:

```python3
#! /usr/bin/env python3
import pandas as pd

from finx.client import FinXClient, ClientTypes

finx_client = FinXClient(
    ClientTypes.socket, finx_api_key="your-api-key", finx_api_url="api-url"
)
finx_client.load_functions()  # Initialize the SDK and refresh all functions with most recent API parameters
function_list = finx_client.list_api_functions()

finx_client.cleanup()  # Make sure to close the socket and daemon thread

df = pd.DataFrame(function_list)
df
```
### FinX Rest Usage:

Unlike the socket api, the FinX Rest API can interact with standardized
batch processes on the FinX Platform.

For instance, the rest api can upload the FinX private data excel template to import new securities to the platform.
Additionally, this client can post the batch job excel data template OR manually configure the tasks using a holdings
file and a dictionary of configurations.

```python3
#! /usr/bin/env python3
import pandas as pd

from finx.client import FinXClient, ClientTypes

finx_client = FinXClient(
    ClientTypes.rest, finx_api_key="your-api-key", finx_api_url="api-url"
)
finx_client.load_functions()  # Initialize the SDK and refresh all functions with most recent API parameters
function_list = finx_client.list_api_functions()

# private data template upload
finx_client.upload_private_data("path/to/private/data/template.xlsx", test_data=True)

# post batch job
finx_client.submit_batch_run("path/to/batch/job/template.xlsx")
# run batch job
finx_client.run_batch_holdings(
    "path/to/holdings/file.xlsx", 
    {
        "ReferenceData": {
            "parse_collateral": True
        },
        "RunCashFlowScenario": {
            "shock_value": 0.,
            "include_cashflows": True,
            "skip_projections": False
        }
    }
)

finx_client.cleanup()  # Make sure to close the socket and daemon thread

df = pd.DataFrame(function_list)
df
```

### FinX Context Manager Usage

One of the perks of using the SDK in an async context is that we can manager some of the initial steps as part of the
async initialization.  Specifically, there is no need to call `load_functions` or `cleanup` 
as part of the async context.

```python3
#! /usr/bin/env python3

from finx.clients import rest_client, socket_client

async def sample_fn():
    async with socket_client.FinXSocketClient() as finx_socket:
        result = await finx_socket.calculate_greeks(101, 100, 0.01, 0.1, 0.0, 0.25, 5.0)
        print(f"Context manager results: {result=}")
    async with rest_client.FinXRestClient() as finx_rest:
        result2 = await finx_rest.calculate_greeks(101, 100, 0.01, 0.1, 0.0, 0.25, 5.0)
        print(f"Context manager results2: {result2=}")
```

Full **Documentation** with all available functions is available at [FinX Docs](https://finx-capital-markets.gitbook.io/)

---
title: FinX Python SDK
tags: technology, documentation, python
---
