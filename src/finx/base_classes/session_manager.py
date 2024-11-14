#! python
"""
author: dick mule
purpose: base class for AIOHTTP session manager
"""
from typing import Any, Optional

import aiohttp

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
            self._session = aiohttp.ClientSession()
        super().model_post_init(__context)

    async def __aenter__(self):
        """
        Entrance method that initializes a session - forces usage within a with statement

        >>> with SessionManager() as session:
        >>>     # Do something with session

        :return: Session Manager Class
        :rtype: SessionManager
        """
        if not self._session:
            self._session = aiohttp.ClientSession()
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

    async def post(self, url: str, **kwargs):
        """
        Call an endpoint with a POST request asynchronously

        :param url: String URL of the endpoint
        :type url: str
        :param kwargs: Data to be sent to the endpoint
        :type kwargs: dict
        :return: dictionary of the response
        :rtype: dict
        """
        async with self._session.post(url, data=kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()

    async def get(self, url: str, **kwargs):
        """
        Call an endpoint with a GET request asynchronously

        :param url: String URL of the endpoint
        :type url: str
        :param kwargs: Data to be sent to the endpoint
        :type kwargs: dict
        :return: dictionary of the response
        :rtype: dict
        """
        async with self._session.get(url, params=kwargs) as resp:
            resp.raise_for_status()
            return await resp.json()
