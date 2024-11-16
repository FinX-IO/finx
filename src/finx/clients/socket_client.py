#! python
"""
author: dick mule
purpose: FinX Socket Client
"""
from threading import Thread
from traceback import format_exc
from typing import Any, Callable, Optional
from uuid import uuid4

import json
import os
import time

from pydantic import PrivateAttr
from websocket import WebSocketApp, enableTrace

import pandas as pd

from finx.base_classes.base_client import BaseFinXClient
from finx.base_classes.context_manager import CacheLookup
from finx.utils.concurrency import hybrid
from finx.utils.payload_parsing import get_size


enableTrace(os.environ.get('ENABLE_SOCKET_TRACE') == 'True')


class FinXWebSocket(WebSocketApp):

    @property
    def is_connected(self):
        return self.sock is not None and self.sock.connected


class FinXSocketClient(BaseFinXClient):
    _awaiting_auth: bool = PrivateAttr(False)
    _is_authenticated: bool = PrivateAttr(False)
    _socket: Optional[FinXWebSocket] = PrivateAttr(None)
    _socket_thread: Optional[Thread] = PrivateAttr(None)

    @property
    def ws_url(self):
        """
        Get the websocket URL

        :return: Websocket URL
        :rtype: str
        """
        return (
            self.context.api_url
                .replace('https', 'wss')
                .replace('http', 'ws')
                .replace('/api/', '/ws/api/')
        )

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic base method that initializes all fields

        :param __context: Context information for pydantic
        :type __context: Any
        :return: None type
        :rtype: None
        """
        super().model_post_init(__context)
        if not self._socket:
            self._run_socket()
        if not self.is_authenticated:
            print('Awaiting authentication...')
            i = 5000
            while not self.is_authenticated and i >= 1:
                time.sleep(.001)
                i -= 1
            if not self.is_authenticated:
                raise Exception('Client not authenticated')

    def cleanup(self):
        """
        Cleanup method

        :return: None type
        :rtype: None
        """
        if self._socket:
            self._socket.close()

    @property
    def is_ssl(self) -> bool:
        """
        Check if the socket is SSL

        :return: Boolean value of SSL status
        :rtype: bool
        """
        return 'https' in self.context.api_url

    @property
    def is_authenticated(self) -> bool:
        """
        Check if the socket is authenticated

        :return: Boolean value of authentication status
        :rtype: bool
        """
        return self._is_authenticated

    def authenticate(self, s: FinXWebSocket):
        """
        Authenticate the socket connection

        :param s: Socket
        :type s: FinXWebSocket
        :return: None type
        :rtype: None
        """
        print('Authenticating...')
        if not self._awaiting_auth:
            self._awaiting_auth = True
            s.send(json.dumps({'finx_api_key': self.context.api_key}))

    def _wrap_on_open(self):
        """
        Wrap on open function so that it binds to self

        :return: Callable on open function for FinXWebSocket
        :rtype: callable[FinXWebSocket]
        """

        def on_open(s: FinXWebSocket):
            print(f'Socket opened: {s.is_connected}')
            self.authenticate(s)

        return on_open

    def __handle_authentication(self):
        """
        Handle authentication

        :return: None type
        :rtype: None
        """
        print('Successfully authenticated')
        self._is_authenticated = True
        self._awaiting_auth = False

    def _wrap_on_message(self):
        """
        Wrap on message function so that it binds to self

        :return: Callable on message function for FinXWebSocket
        :rtype: callable[FinXWebSocket, str]
        """

        def on_message(s: FinXWebSocket, message: str):
            try:
                message = json.loads(message)
                if message.get('is_authenticated') and not self.is_authenticated:
                    return self.__handle_authentication()
                if (job_id := message.get('job_id')) is not None and self._payload_cache:
                    self.update_payload_cache(job_id, *list(self._payload_cache)[1:])
                    return
                if (error := message.get('error')) is not None:
                    print(f'API returned error: {error}')
                    data = error
                else:
                    data = message.get('data', message.get('message', {}))
                data_type = type(data)
                if data_type is not list and (data_type is not dict or data.get('progress') is not None):
                    print(message)
                    return None
                if (cache_keys := message.get('cache_key')) is None:
                    return None
                is_list_of_dicts = data_type is list and isinstance(data[0], dict)
                for key in cache_keys:
                    if is_list_of_dicts and key[0] is not None:
                        value = next(
                            (item for item in data if item.get("security_id", '') in key[1]),
                            None
                        )
                    else:
                        value = data
                    self.context.cache[key[1]][key[2]] = value
            except Exception as e:
                print(f'Socket ({s.is_connected}) on_message error: {format_exc()}, {message}')
                print(f'Error: {e}')
            return None

        return on_message

    def _wrap_on_error(self) -> Callable[[FinXWebSocket, Exception], None]:
        """
        Wrap on error function so that it binds to self

        :return: Callable on error function for FinXWebSocket
        :rtype: callable[FinXWebSocket, Exception]
        """

        def on_error(s: FinXWebSocket, error: Exception):
            """
            On error function

            :param s: Socket
            :type s: FinXWebSocket
            :param error: Error
            :type error: Exception
            :return: None type
            :rtype: None
            """
            print(f'Error on socket ({s.is_connected=}/{self.is_authenticated=}): {error}')

        return on_error

    def _wrap_on_close(self) -> Callable[[FinXWebSocket, Any, Any], None]:
        """
        Wrap on close function so that it binds to self

        :return: Callable on close function for FinXWebSocket
        :rtype: callable[FinXWebSocket]
        """

        def on_close(s: FinXWebSocket, status_code: int, message: str) -> None:
            """
            On close function

            :param s: Socket
            :type s: FinXWebSocket
            :return: None type
            :rtype: None
            """
            print(f'Socket closed: {status_code=}/{message=}')
            self._is_authenticated = False
            self._socket_thread = None
            self._socket = None
            s.close()

        return on_close

    def _parse_batch_input(
            self,
            batch_input: Any,
            base_cache_payload: dict
    ) -> tuple[list[CacheLookup], list[dict], list[dict]]:
        """
        Parse batch input

        :param batch_input: Batch input
        :type batch_input: Any
        :param base_cache_payload: Base cache payload
        :type base_cache_payload: dict
        :return: Cache keys, cached responses, outstanding requests
        :rtype: tuple[list[CacheLookup], list[dict], list[dict]]
        """
        print('Parsing batch input...')
        cache_keys: list[CacheLookup] = []
        batch_input_df = [pd.DataFrame, pd.read_csv][isinstance(batch_input, str)](batch_input)
        for security_input in batch_input_df.to_dict('records'):
            cache_lookup = self.context.check_cache(
                **(base_cache_payload | security_input)
            )
            cache_keys.append(cache_lookup)
        batch_input_df['cache_keys'] = cache_keys
        batch_input_df['cached_responses'] = batch_input_df['cache_keys'].map(lambda x: x.value)
        cached_responses = batch_input_df.loc[
            batch_input_df['cached_responses'].notnull()
        ]['cached_responses'].tolist()
        outstanding_requests = batch_input_df.loc[batch_input_df['cached_responses'].isnull()]
        return cache_keys, cached_responses, outstanding_requests.to_dict(orient='records')

    def _run_socket(self):
        """
        Run the socket connection

        :return: None type
        :rtype: None
        """
        try:
            self._socket = FinXWebSocket(
                self.ws_url,
                on_open=self._wrap_on_open(),
                on_message=self._wrap_on_message(),
                on_error=self._wrap_on_error(),
                on_close=self._wrap_on_close()
            )
            print(f'Connecting to {self.ws_url} ...')

            def run_socket_forever(*args, **kwargs) -> None:
                print('Running socket forever')
                completed = self._socket.run_forever(*args, **kwargs)
                print(f'Socket completed: {completed}')

            self._socket_thread = Thread(
                target=run_socket_forever,
                daemon=False,
                kwargs={
                    'skip_utf8_validation': True,
                    'sslopt': {'check_hostname': False}
                }
            )
            self._socket_thread.start()
        except Exception as e:
            raise Exception(f'Failed to connect to {self.ws_url}: {e}')

    def _upload_batch_file(self, batch_input: Any) -> str:
        """
        Upload a batch file to the API

        :param batch_input: Batch input
        :type batch_input: Any
        :return: Filename of the batch file
        :rtype: str
        """
        filename = f'{uuid4()}.csv'
        batch_type = type(batch_input)
        if batch_type in [pd.DataFrame, pd.Series]:
            batch_input.to_csv(filename, index=False)
        elif batch_type is list:
            if type(batch_input[0]) in [dict, list]:
                request_dicts = [
                    x for x in [
                        y.get("request") for y in batch_input if isinstance(y, dict)
                    ] if x
                ]
                if request_dicts:
                    with open(filename, 'w+') as file:
                        file.write('\n'.join(request_dicts))
                    file.close()
                    print("MADE BATCH FILE")
                else:
                    pd.DataFrame(batch_input).to_csv(filename, index=False)
            elif type(batch_input[0]) is str:
                with open(filename, 'w+') as file:
                    file.write('\n'.join(batch_input))
        print(f'{filename=}')
        return self.upload_file(filename, remove_file=True)

    @hybrid
    async def _dispatch(self, api_method: str, **kwargs) -> dict:
        """
        Dispatch a request to the API

        :param api_method: API method to call
        :type api_method: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Response from the API
        :rtype: dict
        """
        assert self._socket, 'Socket not initialized'
        assert self.is_authenticated, 'Socket not authenticated'
        is_batch: bool = kwargs.pop('is_batch', False)
        callback: callable = kwargs.pop('callback', None)
        payload: dict = {'api_method': api_method}
        if any(kwargs):
            payload.update({
                key: value for key, value in kwargs.items()
                if key != 'finx_api_key' and key != 'api_method'
            })
        if self._payload_cache:
            payload.update(self._payload_cache.payload)
            payload['monitor_hash_key'] = self._payload_cache.job_id
            self._socket.send(json.dumps(payload))
            results = await self._listen_for_results(self._payload_cache.cache_keys, callback, **kwargs)
            self._payload_cache = None
            return results
        payload_size: int = get_size(payload)
        chunk_payload: bool = payload_size > 1e5
        cache_keys: list[CacheLookup] = []
        need_to_batch: bool = is_batch or chunk_payload
        if not need_to_batch:
            cache_lookup: CacheLookup = self.context.check_cache(**payload)
            if cache_lookup.value is not None:
                print('Request found in cache')
                if callable(callback):
                    return callback(cache_lookup.value, **kwargs, cache_keys=cache_lookup)
                return cache_lookup.value
            cache_keys.append(cache_lookup)
        else:
            total_requests: int = 1
            batch_input = kwargs.pop('batch_input', None)
            base_cache_payload: dict = kwargs.copy()
            base_cache_payload['api_method'] = api_method
            if chunk_payload:
                cache_keys.append(self.context.check_cache(**payload))
                cached_responses = []
                outstanding_requests = [payload]
            else:
                cache_keys, cached_responses, outstanding_requests = self._parse_batch_input(
                    batch_input, base_cache_payload
                )
                total_requests = len(cached_responses) + len(outstanding_requests)
            print(f'total requests = {total_requests}')
            if len(cached_responses) == total_requests:
                print(f'All {total_requests} requests found in cache')
                if callable(callback):
                    return callback(cached_responses, **kwargs, cache_keys=cache_keys)
                return cached_responses
            print(f'{len(cached_responses)} out of {total_requests} requests found in cache')
            payload['api_method'] = 'batch_' + api_method
            payload['batch_input'] = outstanding_requests if not chunk_payload else self._upload_batch_file(
                [[payload], outstanding_requests][batch_input is not None]
            )
            payload = {k: v for k, v in payload.items() if k in ['batch_input', 'api_method']}
            payload.update({k: v for k, v in kwargs.items() if k != 'request'})
            payload['run_batch'] = is_batch
        payload['cache_key'] = [list(x) for x in cache_keys if x.value is None]
        if need_to_batch:
            self.update_payload_cache("", payload, cache_keys)
        try:
            self._socket.send(json.dumps(payload))
        except Exception as e:
            for k, v in payload.items():
                print(f'{k}: {str(v)[:1000]}')
            raise Exception(f'Failed to serialize payload')
        results = await self._listen_for_results(cache_keys, callback, **kwargs)
        self._payload_cache = None
        return results

    @hybrid
    async def _batch_dispatch(self, api_method: str, batch_params: list[dict], **kwargs) -> list[dict]:
        """
        Abstract batch request dispatch function. Issues a request for each input

        :param api_method: API method to call
        :type api_method: str
        :param batch_params: List of security parameters
        :type batch_params: list[dict]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Response from the API
        :rtype: list[dict]
        """
        return self._dispatch(
            api_method,
            batch_input=batch_params,
            **kwargs,
            is_batch=True
        )
