#! python
"""
author: dick mule
purpose: Expose FinX Clients for API usage
"""
from typing import Union

from finx.base_classes.base_client import BaseFinXClient, ApiContextManager
from finx.clients import rest_client, socket_client
from finx.utils.enums import ComparatorEnum


class ClientTypes(ComparatorEnum):
    rest = 0
    socket = 1

    @staticmethod
    def from_int(i: int) -> 'ClientTypes':
        """
        Return name from index

        :param i: Index of enum
        :type  i: int
        :return: Name of enum
        :rtype: str
        """
        return ClientTypes.list()[int(i)]


class _FinXClientFactory:
    __instance: "_FinXClientFactory" = None
    __context_manager: ApiContextManager = None

    def __new__(cls, *args, **kwargs):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls, **kwargs)
        return cls.__instance

    def set_credentials(self, finx_api_key: str = None, finx_api_endpoint: str = None):
        context_params = {'api_key': finx_api_key, 'api_url': finx_api_endpoint}
        if not self.__context_manager:
            self.__context_manager = ApiContextManager(**context_params)
            return
        if finx_api_key:
            self.__context_manager.api_key = finx_api_key
        if finx_api_endpoint:
            self.__context_manager.api_url = finx_api_endpoint

    def __call__(self, client_type: Union[str, ClientTypes] = 'socket', *args, **kwargs) -> 'BaseFinXClient':
        if isinstance(client_type, str):
            client_type = ClientTypes.get(client_type)
        if isinstance(client_type, int):
            client_type = ClientTypes.from_int(client_type)
        self.set_credentials(kwargs.pop('finx_api_key', None), kwargs.pop('finx_api_endpoint', None))
        if client_type is ClientTypes.rest:
            return rest_client.FinXRestClient.from_kwargs(context=self.__context_manager, **kwargs)
        return socket_client.FinXSocketClient.from_kwargs(context=self.__context_manager, **kwargs)


FinXClient = _FinXClientFactory()
