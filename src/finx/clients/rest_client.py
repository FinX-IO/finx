#! python
"""
author: dick mule
purpose: FinX Rest Client
"""
from typing import Any

from finx.base_classes.base_client import BaseFinXClient, SessionManager
from finx.base_classes.context_manager import CacheLookup
from finx.utils.concurrency import hybrid
from finx.utils.task_runner import TaskRunner


class FinXRestClient(BaseFinXClient):
    """
    FinX Rest Client Interface
    """

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic base method that initializes all fields

        :param __context: Context information for pydantic
        :type __context: Any
        :return: None type
        :rtype: None
        """
        super().model_post_init(__context)

    def _unpack_session_response(self, data: dict, cache_lookup: CacheLookup) -> dict:
        """

        :param data: Dict of data from the API
        :type data: dict
        :param cache_lookup: Cache lookup object
        :type cache_lookup: CacheLookup
        :return: Data from the API
        :rtype: dict
        """
        if (error := data.get('error')) is not None:
            print(f'API returned error: {error}')
            return error
        if isinstance(data.get('data'), dict) and data.get('data', dict()).get('filename'):
            data = self.download_file(data['data'])
        self.cache[cache_lookup.key] = data
        return data

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
        payload: dict = {
            'api_key': self.context.api_key,
            'api_method': api_method
        }
        if any(kwargs):
            payload.update({
                key: value for key, value in kwargs.items()
                if key not in ['finx_api_key', 'api_method']
            })
        cache_lookup = self.context.check_cache(api_method, **kwargs)
        if cache_lookup.value is not None:
            return cache_lookup.value
        if not self.session:
            async with SessionManager() as session:
                data = await session.post(self.context.api_url, **payload)
                return self._unpack_session_response(data, cache_lookup)
        data = await self.session.post(self.context.api_url, **payload)
        return self._unpack_session_response(data, cache_lookup)

    @hybrid
    async def _dispatch_batch(self, api_method: str, security_params: list[dict], **kwargs) -> list[dict]:
        """
        Abstract batch request dispatch function. Issues a request for each input

        :param api_method: API method to call
        :type api_method: str
        :param security_params: List of security parameters
        :type security_params: list[dict]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Response from the API
        :rtype: list[dict]
        """
        assert api_method != 'list_api_functions' \
               and type(security_params) is list \
               and len(security_params) < 100
        runner = TaskRunner(async_func=self._dispatch, concurrency_type='async')
        return runner.run_concurrently(
            [{'api_method': api_method} | params for params in security_params],
            **kwargs
        )
