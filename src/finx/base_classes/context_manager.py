#! python
"""
author: dick mule
purpose: Base Context Manager for FinX SDK
"""
from typing import Any, NamedTuple, Optional

import asyncio
import gc as garbage_collector
import os

from pydantic import Field

from finx.base_classes.from_kwargs import BaseMethods
from finx.utils.enums import ExtendedEnum

# pylint: disable=no-member


class _ParamCacheKeys(ExtendedEnum):
    """Keys to check in Cache"""

    security_id = 1
    as_of_date = 2
    api_method = 3
    input_file = 4
    output_file = 5


class CacheLookup(NamedTuple):
    """A named tuple for cache lookup values"""

    value: dict
    key: str
    param_key: str


class ApiContextManager(BaseMethods):
    """
    Context manager that manages the api key, endpoint configurations, and the results cache
    """

    api_key: Optional[str] = Field(None, hidden=True, repr=False)
    api_url: Optional[str] = Field(None, hidden=True, repr=False)
    cache_size: int = Field(100000, repr=False)
    cache: dict[str, dict[str, dict]] = Field(default_factory=dict, repr=False)
    timeout: int = Field(100, repr=False)
    event_loop: asyncio.AbstractEventLoop = Field(
        default_factory=asyncio.get_event_loop, repr=False
    )

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic callback that allows all fields to be validated on class instantiation

        :param __context: Pydantic context info
        :type __context: Any
        :return: None type object
        :rtype: None
        """
        self.api_key = self.api_key or os.environ.get("FINX_API_KEY")
        if not self.api_key:
            raise ValueError(
                "API Key not found - please include the keyword argument "
                "finx_api_key or set the environment variable FINX_API_KEY"
            )
        self.api_url = self.api_url or os.environ.get("FINX_API_URL")
        if not self.api_url:
            raise ValueError(
                "API URL not found - please include the keyword argument "
                "finx_api_endpoint or set the environment variable FINX_API_URL"
            )
        if self.api_url[-1] != "/":
            self.api_url += "/"
        if "api/" not in self.api_url:
            self.api_url += "api/"
        super().model_post_init(__context)

    def clear_cache(self) -> None:
        """
        Clear the cache and run the garbage collector

        :return: None type
        :rtype: None
        """
        self.cache.clear()
        garbage_collector.collect()

    @staticmethod
    def _cache_key_from_kwargs(api_method: str, **kwargs) -> str:
        """
        Create a cache key from the kwargs

        :param api_method: Name of the API method
        :type api_method: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Cache key
        :rtype: str
        """
        security_id = kwargs.get("security_id")
        as_of_date = kwargs.get("as_of_date")
        cache_key = (
            f'{f"{security_id}:{as_of_date}:" if security_id else ""}{api_method}'
        )
        return cache_key

    def check_cache(self, api_method: str, **kwargs) -> CacheLookup:
        """
        Check the cache for a value

        :param api_method: Name of the API method
        :type api_method: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Cache lookup object
        :rtype: CacheLookup
        """
        params: dict = {} if not kwargs else kwargs
        cache_key: str = self._cache_key_from_kwargs(api_method, **params)
        params_key: str = (
            ",".join(
                [
                    f"{key}:{params[key]}"
                    for key in sorted(params.keys())
                    if key not in _ParamCacheKeys.list()
                ]
            )
            or "NONE"
        )
        cached_value = self.cache.get(cache_key, {}).get(params_key)
        if cached_value is None:
            # pylint: disable=unsupported-assignment-operation
            self.cache[cache_key] = {}
            # pylint: disable=unsubscriptable-object
            self.cache[cache_key][params_key] = None
        return CacheLookup(cached_value, cache_key, params_key)
