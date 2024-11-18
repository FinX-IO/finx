#! python
"""
author: dick mule
purpose: base class for AIOHTTP session manager
"""
import asyncio

from io import StringIO
from typing import Any, Optional

import aiohttp
import pandas as pd

from pydantic import BaseModel, PrivateAttr


class SessionManager(BaseModel):
    """
    Class that can be used to manage an AIOHTTP Session for use in asynchronous endpoint requests
    """
    _session: Optional[aiohttp.ClientSession] = PrivateAttr(None)

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic base method that initializes all fields

        :param __context: Context information for pydantic
        :type __context: Any
        :return: None type
        :rtype: None
        """
        if not self._session:
            self._session = aiohttp.ClientSession(headers={'content-type': 'application/json'})
        super().model_post_init(__context)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """
        Update event loop for session

        :param loop: Event loop to be set
        :type loop: asyncio.AbstractEventLoop
        :return: None type
        :rtype: None
        """
        self._session.loop = loop

    async def __aenter__(self):
        """
        Entrance method that initializes a session - forces usage within a with statement

        >>> with SessionManager() as session:
        >>>     # Do something with session

        :return: Session Manager Class
        :rtype: SessionManager
        """
        if not self._session:
            self._session = aiohttp.ClientSession(headers={'content-type': 'application/json'})
        return self

    async def __aexit__(self, *err):
        """
        Exit method that closes session after with statement is terminated

        :param err: Error information
        :type err: tuple
        :return: None type
        :rtype: None
        """
        if not self._session:
            return
        await self._session.close()
        self._session = None

    async def post(self, url: str, is_json_response: bool = True, is_json_data: bool = False, **kwargs):
        """
        Call an endpoint with a POST request asynchronously

        :param url: String URL of the endpoint
        :type url: str
        :param is_json_response: Boolean flag to determine if the response is JSON
        :type is_json_response: bool
        :param kwargs: Data to be sent to the endpoint
        :type kwargs: dict
        :return: dictionary of the response
        :rtype: dict
        """
        print(f'POSTING TO {url} with {kwargs} / {self._session.headers}')
        async with self._session.post(url, json=kwargs) as resp:
            resp.raise_for_status()
            if is_json_response:
                return await resp.json()
            return pd.read_csv(
                StringIO((await resp.content.read()).decode('utf-8')),
                engine='python',
                converters={'security_id': str}
            )

    async def get(self, url: str, is_json_response: bool = True, **kwargs):
        """
        Call an endpoint with a GET request asynchronously

        :param url: String URL of the endpoint
        :type url: str
        :param is_json_response: Boolean flag to determine if the response is JSON
        :type is_json_response: bool
        :param kwargs: Data to be sent to the endpoint
        :type kwargs: dict
        :return: dictionary of the response
        :rtype: dict
        """
        async with self._session.get(url, params=kwargs) as resp:
            resp.raise_for_status()
            if is_json_response:
                return await resp.json()
            return pd.read_csv(
                StringIO((await resp.content.read()).decode('utf-8')),
                engine='python',
                converters={'security_id': str}
            )
