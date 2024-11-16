#! python
"""
author: dick mule
purpose: Base Client interface that underpins REST and SOCKET implementations
"""
from abc import abstractmethod, ABC
from io import StringIO
from traceback import format_exc
from types import MethodType
from typing import Any, Optional

import os
import json
import time
import weakref

import pandas as pd
import requests

from pydantic import Field, PrivateAttr

from finx.base_classes.context_manager import ApiContextManager
from finx.base_classes.from_kwargs import BaseMethods
from finx.base_classes.session_manager import SessionManager
from finx.utils.concurrency import hybrid, Hybrid

_BATCH_INPUTS = 'batch_params=None, input_file=None, output_file=None, '
_BATCH_PARAMS = 'batch_params=batch_params, input_file=input_file, output_file=output_file, '


class BaseFinXClient(BaseMethods, ABC):
    """
    Base FinX Client interface - will initialize a context manager and session manager
    """
    context: Optional[ApiContextManager] = Field(None, repr=False)
    session: Optional[SessionManager] = Field(None, repr=False)
    finalized: Optional[weakref.finalize] = None
    last_job: str = Field(None, repr=False)
    _cleaned_up: bool = PrivateAttr(False)

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic base method that initializes all fields

        :param __context: Context information for pydantic
        :type __context: Any
        :return: None type
        :rtype: None
        """
        if not self.context:
            self.context = ApiContextManager(**self.extra_attrs)
        self.finalized = weakref.finalize(self, self.free)
        super().model_post_init(__context)
        for k in dir(self):
            if '__' in k:
                continue
            v = getattr(self, k)
            if isinstance(v, Hybrid):
                v.set_event_loop(self.context.event_loop)

    def cleanup(self):
        """
        Require any inheritable class to clean up the c++ object

        :return: None type object
        :rtype: None
        """

    def free(self):
        """
        Free the c++ object

        :return: None type object
        :rtype: None
        """
        if not self._cleaned_up:
            self.cleanup()
            self._cleaned_up = True

    def __del__(self):
        """
        Destructor to ensure that any thread/socket resources are freed

        :return: None type object
        :rtype: None
        """
        if getattr(self, "finalized", None) is None:
            return
        self.free()

    @staticmethod
    def _parse_request_response(response: requests.Response, is_json: bool = False) -> dict | pd.DataFrame:
        """
        Parse the response from a request

        :param response: Response from a request
        :type response: requests.Response
        :return: Parsed response
        :rtype: dict | pd.DataFrame
        """
        response = response.content.decode('utf-8')
        if is_json:
            response = json.loads(response)
        else:
            response = pd.read_csv(
                StringIO(response),
                engine='python',
                converters={'security_id': str}
            )
        return response

    def _reload_function_definitions(self, all_functions: dict[str, Any] | list[Any]) -> None:
        if isinstance(all_functions, dict):
            all_functions = all_functions['data']
        for function in all_functions:
            name, required, optional = [function[k] for k in ["name", "required", "optional"]]
            required_str = (", ".join(required) + ", ") if required else ""
            required_zip = (", ".join([f"{x}={x}" for x in required]) + ", ") if required else ""
            optional_str = (", ".join([f'{k}={v}' for k, v in optional.items()]) + ", ") if optional is not None else ""
            optional_zip = (", ".join([f"{x}={x}" for x in optional.keys()]) + ", ") if optional is not None else ""
            local_vals = locals() | {'hybrid': hybrid}
            for index, batch in enumerate(["batch_", ""]):
                inputs = [_BATCH_INPUTS, f"{required_str}{optional_str}"][index]
                params = [_BATCH_PARAMS, f"{required_zip}{optional_zip}"][index]
                string_repr = (
                    f'async def {batch}{name}(self, {inputs}**kwargs):\n'
                    f'    result = await self._{batch}dispatch("{f"{name}"}", {params}**kwargs)\n'
                    f'    if not isinstance(result, (list, dict)):\n'
                    f'        return await result\n'
                    f'    return result'
                )
                exec(string_repr, local_vals)
                self.__dict__[f'{batch}{name}'] = hybrid(MethodType(local_vals[f'{batch}{name}'], self))
                self.__dict__[f'{batch}{name}'].set_event_loop(self.context.event_loop)

    @hybrid
    async def download_file(
            self,
            filename: str,
            bucket_name: str = None,
            use_async: bool = True,
            is_json_response: bool = False
    ) -> dict | pd.DataFrame:
        """
        Download a file from the API

        :param filename: Name of the file to download
        :type filename: str
        :param bucket_name: Bucket name to download from
        :type bucket_name: str
        :param use_async: Use async method
        :type use_async: bool
        :param is_json_response: Response is JSON
        :type is_json_response: bool
        :return: File contents
        :rtype: dict | pd.DataFrame
        """
        if not use_async:
            return self._parse_request_response(
                requests.get(
                    f'{self.context.api_url}batch-download/',
                    params={'filename': filename, 'bucket_name': bucket_name}
                ),
                is_json_response
            )
        if not self.session:
            async with SessionManager() as session:
                result = await session.get(
                    f'{self.context.api_url}batch-download/',
                    is_json_response=is_json_response,
                    filename=filename,
                    bucket_name=bucket_name
                )
            return result
        return await self.session.get(
            f'{self.context.api_url}batch-download/',
            is_json_response=is_json_response,
            filename=filename,
            bucket_name=bucket_name
        )

    def upload_file(self, filename: str, remove_file: bool = False) -> dict:
        """
        Download a file from the API

        :param filename: Name of the file to download
        :type filename: str
        :param remove_file: Remove temporary file
        :type remove_file: bool
        :return: File contents
        :rtype: dict | pd.DataFrame
        """
        file = open(filename, 'rb')
        # Upload file to server and record filename
        response = requests.post(
            f'{self.context.api_url}batch-upload/',
            data={'finx_api_key': self.context.api_key, 'filename': filename},
            files={'file': file}
        ).json()
        file.close()
        if remove_file:
            os.remove(filename)
        if response.get('failed'):
            raise Exception(f'Failed to upload file: {response["message"]}')
        print('Batch file uploaded')
        return response.get('filename', filename)

    @hybrid
    async def _download_file_results(self, file_results: list[tuple[int, dict]]) -> pd.DataFrame:
        """
        Download file results from the API

        :param file_results: File results
        :type file_results: list[tuple[int, dict]]
        :return: File results
        :rtype: pd.DataFrame
        """
        downloaded_files = dict()
        files_to_download = [
            dict(s) for s in set(
                frozenset(d.items())
                for d in list(map(lambda x: x[1], file_results))
            )
        ]
        for file in files_to_download:
            downloaded_files[file['filename']] = await self.download_file(**file, use_async=False)
        return downloaded_files

    @hybrid
    async def _wait_for_results(self, cache_keys: list[list[str]]) -> tuple[list[Any], list[tuple[int, dict]]]:
        """
        Function to monitor keys and wait til all results are available

        :param cache_keys: List of cache keys
        :type cache_keys: list[list[str]]
        :return: tuple of results and file results
        :rtype: tuple[list[Any], list[tuple[int, dict]]]
        """
        remaining_keys = cache_keys
        while len(remaining_keys):
            time.sleep(0.05)
            remaining_results = [self.context.cache.get(key[1], dict()).get(key[2], None) for key in remaining_keys]
            remaining_keys = [remaining_keys[i] for i, value in enumerate(remaining_results) if value is None]
        file_results: list[tuple[int, dict]] = []
        results: list[Any] = [self.context.cache.get(key[1], dict()).get(key[2], None) for key in cache_keys]
        for i, result in enumerate(results):
            if not isinstance(result, dict):
                continue
            if result.get('filename'):
                file_results.append((i, result))
        if not file_results:
            return results, file_results
        downloaded_files = await self._download_file_results(file_results)
        for index, file_result in file_results:
            file_df = downloaded_files[file_result['filename']]
            if 'cache_key' not in file_df:
                matched_result = file_df
            else:
                matched_result = file_df.loc[
                    file_df['cache_key'].map(lambda x: json.loads(x) == list(cache_keys[index]))
                ].to_dict(orient='records')[0]
            if 'filename' in matched_result:
                matched_result['result'] = await self.download_file(**matched_result)
                matched_result = {
                    k: matched_result[k] for k in ['security_id', 'result', 'cache_key']
                }
            self.context.cache[cache_keys[index][1]][cache_keys[index][2]] = matched_result
            results[index] = matched_result
        return results, file_results

    @hybrid
    async def _listen_for_results(self, cache_keys: list[list[str]], callback: callable = None, **kwargs):
        """
        Listen for results from the API

        :param cache_keys: List of cache keys
        :type cache_keys: list[list[str]]
        :param callback: Callback function to process results
        :type callback: callable
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: Any
        """
        try:
            results, file_results = await self._wait_for_results(cache_keys)
            if (
                    (output_file := kwargs.get('output_file')) is not None and
                    len(results) > 0 and type(results[0]) in [list, dict]
            ):
                print(f'Writing data to {output_file}')
                pd.DataFrame(results).to_csv(output_file, index=False)
            if callable(callback):
                return callback(results, **kwargs, cache_keys=cache_keys)
            return results if len(results) > 1 else results[0] if len(results) > 0 else results
        except Exception as e:
            print(f'Failed to find result/execute callback: {format_exc()}')
            print(f'Exception: {e}')

    @abstractmethod
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

    @abstractmethod
    @hybrid
    async def _batch_dispatch(self, api_method: str, batch_params: list[dict], **kwargs) -> list[dict]:
        """
        Abstract batch request dispatch function. Issues a request for each input

        :param api_method: API method to call
        :type api_method: str
        :param batch_params: List of api parameters
        :type batch_params: list[dict]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Response from the API
        :rtype: list[dict]
        """

    @hybrid
    async def load_functions(self):
        all_functions = await self._dispatch('list_api_functions')
        self._reload_function_definitions(all_functions)
