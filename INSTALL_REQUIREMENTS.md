## FinX SDK Installation

### How to install the FinX Python SDK in various environments
The FinX Python SDK is a public python package available on PyPi.org and can be installed from pip. 
The package will look for 3 environment variables in the python environment:

```[!NOTE]
You can find your FINX_API_KEY and FINX_API_ENDPOINT in the Web App at https://app.finx.io after you log in with your FINX_USER_EMAIL.

Need to register? Visit https://app.finx.io
```

### Python Requirements

The FinX Python SDK will attempt to install the following dependencies:

```requirements.txt
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

### Environment Variables

The FinX SDK will look for the following environment variables with values that are provided by FinX Capital Markets. 
You may find these values in your user account settings, or in the email sent to you upon registration.

1. FINX_API_KEY - The API Key provided by FinX Capital Markets LLC
2. FINX_API_ENDPOINT - The URL of the FinX Platform API.
3. FINX_USER_EMAIL - The email address used to register with FinX.

```bash
#! /bin/bash
export FINX_API_KEY={your_api_key}
export FINX_API_ENDPOINT={your_api_url}
export FINX_USER_EMAIL={your_user_email}
```

### Pipenv Environment Setup

```bash
#! /bin/bash
pip install pipenv
pipenv clean
pipenv install aiohttp setuptools nest-asyncio numpy pandas plotly pytest 
pipenv install requests scipy websocket websocket-client websockets
pipenv install finx-io
pipenv shell
```

#### Setting Environment Variables
```bash
#! pipenv shell
export FINX_API_KEY='{your_api_key}'
export FINX_API_ENDPOINT='{your_api_url}'
export FINX_USER_EMAIL='{your_user_email}'
```

### Connect to FinX
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