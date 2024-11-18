#! /bin/bash
mkdir pipenv-temp && cd pipenv-temp
pipenv clean
pipenv install aiohttp setuptools nest-asyncio numpy pandas plotly pytest requests scipy websocket websocket-client websockets
pipenv install -i https://test.pypi.org/simple/ finx-io==1.0.21
python3 -c "import finx; from finx.client import FinXClient; finx_client = FinXClient('socket', ssl=True); function_list = finx_client.list_api_functions(); print(function_list)"