#! python
"""
author: dick mule
purpose: Base Client interface that underpins REST and SOCKET implementations
"""
from abc import abstractmethod, ABC
from io import StringIO
from traceback import format_exc
from types import MethodType
from typing import Any, NamedTuple, Optional

import asyncio
import logging
import os
import json
import time
import weakref

import pandas as pd
import requests

from pydantic import Field, PrivateAttr

from finx.base_classes.context_manager import ApiContextManager, CacheLookup
from finx.base_classes.from_kwargs import BaseMethods
from finx.base_classes.session_manager import SessionManager
from finx.utils.concurrency import hybrid, Hybrid

_BATCH_INPUTS = "batch_params=None, input_file=None, output_file=None, "
_BATCH_PARAMS = (
    "batch_params=batch_params, input_file=input_file, output_file=output_file, "
)


# pylint: disable=no-member
# pylint: disable=too-many-lines
# pylint: disable=too-many-locals
# pylint: disable=missing-timeout
# pylint: disable=consider-using-with


class PayloadCache(NamedTuple):
    """Payload object to manage state internally"""

    job_id: str
    payload: dict
    cache_keys: list[CacheLookup]


# pylint: disable=too-many-public-methods
class BaseFinXClient(BaseMethods, ABC):
    """
    Base FinX Client interface - will initialize a context manager and session manager

    :meta enable: members

    """

    context: Optional[ApiContextManager] = Field(None, repr=False)
    session: Optional[SessionManager] = Field(None, repr=False)
    finalized: Optional[weakref.finalize] = None
    _payload_cache: Optional[PayloadCache] = PrivateAttr(None)
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
            if "__" in k:
                continue
            v = getattr(self, k)
            if isinstance(v, Hybrid):
                v.set_event_loop(self.context.event_loop)

    def update_payload_cache(
        self, job_id: str, payload: dict, cache_keys: list[CacheLookup]
    ) -> None:
        """
        Update the payload cache

        :param job_id: Job ID
        :type job_id: str
        :param payload: Payload data
        :type payload: dict
        :param cache_keys: Cache keys
        :type cache_keys: list[CacheLookup]
        :return: None type object
        :rtype: None
        """
        self._payload_cache = PayloadCache(job_id, payload, cache_keys)

    def cleanup(self):
        """
        Require any inheritable class to clean up the c++ object

        :return: None type object
        :rtype: None
        """
        if self.session:
            try:
                loop = asyncio.get_event_loop()
                loop.create_task(self.session.cleanup.run_async())
            except RuntimeError:
                loop = asyncio.new_event_loop()
                loop.run_until_complete(self.session.cleanup())

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
    def _parse_request_response(
        response: requests.Response, is_json: bool = False
    ) -> dict | pd.DataFrame:
        """
        Parse the response from a request

        :param response: Response from a request
        :type response: requests.Response
        :return: Parsed response
        :rtype: dict | pd.DataFrame
        """
        response = response.content.decode("utf-8")
        if is_json:
            response = json.loads(response)
        else:
            response = pd.read_csv(
                StringIO(response), engine="python", converters={"security_id": str}
            )
        return response

    def _reload_function_definitions(
        self, all_functions: dict[str, Any] | list[Any]
    ) -> None:
        if isinstance(all_functions, dict):
            all_functions = all_functions["data"]
        for function in all_functions:
            name, required, optional = [
                function[k] for k in ["name", "required", "optional"]
            ]
            required_str = (", ".join(required) + ", ") if required else ""
            required_zip = (
                (", ".join([f"{x}={x}" for x in required]) + ", ") if required else ""
            )
            optional_str = (
                (", ".join([f"{k}={v}" for k, v in optional.items()]) + ", ")
                if optional is not None
                else ""
            )
            optional_zip = (
                (", ".join([f"{x}={x}" for x in optional.keys()]) + ", ")
                if optional is not None
                else ""
            )
            local_vals = locals() | {"hybrid": hybrid, "pd": pd}
            for index, batch in enumerate(["batch_", ""]):
                inputs = [_BATCH_INPUTS, f"{required_str}{optional_str}"][index]
                params = [_BATCH_PARAMS, f"{required_zip}{optional_zip}"][index]
                string_repr = (
                    f"async def {batch}{name}(self, {inputs}**kwargs):\n"
                    f'    result = await self._{batch}dispatch.run_async("{f"{name}"}", {params}**kwargs)\n'
                    f"    if not isinstance(result, (list, dict, pd.DataFrame)):\n"
                    f"        return await result\n"
                    f"    return result"
                )
                exec(string_repr, local_vals)  # pylint: disable=exec-used
                self.__dict__[f"{batch}{name}"] = hybrid(
                    MethodType(local_vals[f"{batch}{name}"], self)
                )
                self.__dict__[f"{batch}{name}"].set_event_loop(self.context.event_loop)

    @hybrid
    async def download_file(
        self,
        filename: str,
        bucket_name: str = None,
        use_async: bool = True,
        is_json_response: bool = False,
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
                    f"{self.context.api_url}batch-download/",
                    params={"filename": filename, "bucket_name": bucket_name},
                ),
                is_json_response,
            )
        if not self.session:
            async with SessionManager() as session:
                result = await session.get(
                    f"{self.context.api_url}batch-download/",
                    is_json_response=is_json_response,
                    filename=filename,
                    bucket_name=bucket_name,
                )
            return result
        return await self.session.get(
            f"{self.context.api_url}batch-download/",
            is_json_response=is_json_response,
            filename=filename,
            bucket_name=bucket_name,
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
        file = open(filename, "rb")
        # Upload file to server and record filename
        logging.debug("Uploading batch file to %sbatch-upload/", self.context.api_url)
        # print(filename, pd.read_csv(filename))
        response = requests.post(
            f"{self.context.api_url}batch-upload/",
            data={"finx_api_key": self.context.api_key, "filename": filename},
            files={"file": file},
        )
        try:
            response = response.json()
        except requests.JSONDecodeError as exc:
            logging.critical(
                "UPLOAD ERROR: status_code=%i -> %s",
                response.status_code,
                response.text,
            )
            if remove_file:
                os.remove(filename)
            raise ValueError("Failed to upload file") from exc
        file.close()
        if remove_file:
            os.remove(filename)
        if response.get("failed"):
            raise ValueError(f'Failed to upload file: {response["message"]}')
        # print("Batch file uploaded")
        return response.get("filename", filename)

    @hybrid
    async def _download_file_results(
        self, file_results: list[tuple[int, dict]]
    ) -> pd.DataFrame:
        """
        Download file results from the API

        :param file_results: File results
        :type file_results: list[tuple[int, dict]]
        :return: File results
        :rtype: pd.DataFrame
        """
        downloaded_files = {}
        files_to_download = [
            dict(s)
            for s in set(
                frozenset(d.items()) for d in list(map(lambda x: x[1], file_results))
            )
        ]
        logging.debug(
            "Downloading %i files files_to_download=%s",
            len(files_to_download),
            files_to_download,
        )
        for file in files_to_download:
            downloaded_files[file["filename"]] = await self.download_file.run_async(
                file["filename"], file.get("bucket_name"), use_async=False
            )
        return downloaded_files

    @hybrid
    async def _wait_for_results(
        self, cache_keys: list[list[str]]
    ) -> tuple[list[Any], list[tuple[int, dict]]]:
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
            remaining_results = [
                self.context.cache.get(key[1], {}).get(key[2], None)
                for key in remaining_keys
            ]
            remaining_keys = [
                remaining_keys[i]
                for i, value in enumerate(remaining_results)
                if value is None
            ]
        file_results: list[tuple[int, dict]] = []
        results: list[Any] = [
            self.context.cache.get(key[1], {}).get(key[2], None) for key in cache_keys
        ]
        for i, result in enumerate(results):
            if not isinstance(result, dict):
                continue
            if result.get("filename"):
                file_results.append((i, result))
        if not file_results:
            return results, file_results
        # print(f"Results found for {len(cache_keys)} keys => {file_results}")
        downloaded_files = await self._download_file_results.run_async(file_results)
        n_results = len(file_results)
        for index, file_result in file_results:
            check_strings = [json.dumps(list(cache_keys[index])), f'{list(cache_keys[index])}']
            print(
                f"\rLoading result[{index + 1} / {n_results}]",
                end=["", "\n"][index == (n_results - 1)],
            )
            file_df = downloaded_files[file_result["filename"]]
            if "cache_key" not in file_df:
                matched_result = file_df
            else:
                matched_result = None
                for key_as_str in check_strings:
                    try:
                        matched_result = file_df.loc[
                            file_df["cache_key"] == key_as_str
                        ].to_dict(orient="records")[0]
                    except IndexError:
                        continue
                if matched_result is None:
                    logging.critical(
                        "Failed to find result for %s in %s",
                        cache_keys[index],
                        file_result["filename"],
                    )
                    raise IndexError(f"Failed to find result[{index}] = {cache_keys[index]}")
            if "filename" in matched_result:
                matched_result["result"] = await self.download_file.run_async(
                    **matched_result
                )
                matched_result = {
                    k: matched_result[k] for k in ["security_id", "result", "cache_key"]
                }
            self.context.cache[cache_keys[index][1]][
                cache_keys[index][2]
            ] = matched_result
            results[index] = matched_result
        return results, file_results

    @hybrid
    async def _listen_for_results(
        self, cache_keys: list[list[str]], callback: callable = None, **kwargs
    ):
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
            results, _ = await self._wait_for_results.run_async(cache_keys)
            if (
                (output_file := kwargs.get("output_file")) is not None
                and len(results) > 0
                and type(results[0]) in [list, dict]
            ):
                logging.debug("Writing data to %s", output_file)
                pd.DataFrame(results).to_csv(output_file, index=False)
            if callable(callback):
                return callback(results, **kwargs, cache_keys=cache_keys)
            return (
                results
                if len(results) > 1
                else results[0] if len(results) > 0 else results
            )
        except Exception as e:  # pylint: disable=broad-exception-caught
            logging.critical("Failed to find result/execute callback: %s", format_exc())
            logging.critical("Exception: %s", e)

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
    async def _batch_dispatch(
        self, api_method: str, batch_params: list[dict], **kwargs
    ) -> list[dict]:
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
        """
        Load all available functions from the API

        :return: None type object
        :rtype: None
        """
        all_functions = await self._dispatch.run_async("list_api_functions")
        self._reload_function_definitions(all_functions)

    @hybrid
    async def list_api_functions(self, **kwargs):
        """
        List all available API functions

        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: List of API functions
        :rtype: list[dict]
        """

    @hybrid
    async def batch_coverage_check(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Returns a list of covered securities for a batch of security ids

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    async def coverage_check(self, security_id, **kwargs):
        """
        Returns a list of covered securities. Check to see if a security id is covered by FinX SecurityDB.

        .. code-block:: python

            >>> # SAMPLE USAGE
            >>> finx_client.coverage_check(security_id='38376R3H7')

        :param security_id: Security ID
        :type security_id: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_list_fixings(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch list fixings function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    async def list_fixings(self, as_of_date=None, currency=None, **kwargs):
        """
        List fixings function

        :param as_of_date: Date to list fixings for
        :type as_of_date: Optional[str]
        :param currency: Currency to list fixings for
        :type currency: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    async def batch_get_fixings(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch get fixings function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    async def get_fixings(self, fixings, as_of_date=None, tenors=None, **kwargs):
        """
        Get fixings function

        :param fixings: List of fixings to get
        :type fixings: list
        :param as_of_date: Date to get fixings for
        :type as_of_date: Optional[str]
        :param tenors: List of tenors to get fixings for (comma separated list)
        :type tenors: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_get_curve(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch get curve function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-positional-arguments
    async def get_curve(
        self,
        curve_name,
        currency,
        start_date,
        end_date=None,
        country_code=None,
        fixing=None,
        tenor=None,
        **kwargs,
    ):
        """
        Get curve function

        :param curve_name: Name of the curve to get
        :type curve_name: str
        :param currency: Currency to get curve for
        :type currency: str
        :param start_date: Start date for curve
        :type start_date: Optional[str]
        :param end_date: End date for curve
        :type end_date: Optional[str]
        :param country_code: Country code
        :type country_code: Optional[str]
        :param fixing: Fixing for curve
        :type fixing: Optional[str]
        :param tenor: Tenor for curve
        :type tenor: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def interpolate_curve(self, t_obs, r_obs, t_new, interpolator=None, **kwargs):
        """
        Interpolate curve function

        :param t_obs: List of observed times
        :type t_obs: list[float]
        :param r_obs: List of observed rates
        :type r_obs: list[float]
        :param t_new: List of new (interpolated) times
        :type t_new: list[float]
        :param interpolator: Interpolator to use
        :type interpolator: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def get_exchange_rate_history(self, currency_list, **kwargs):
        """
        Get exchange rate history function

        :param currency_list: List of currencies to get exchange rate history for
        :type currency_list: list
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def forecast_exchange_rates(
        self, currency_list, as_of_date, post_convert_currency=None, **kwargs
    ):
        """
        Forecast exchange rates function

        :param currency_list: List of currencies to forecast exchange rates for
        :type currency_list: list[str]
        :param as_of_date: Date to forecast exchange rates for
        :type as_of_date: str
        :param post_convert_currency: Currency to convert exchange rates to
        :type post_convert_currency: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def upload_private_data(self, filename, test_data, **kwargs):
        """
        Upload private data function

        :param filename: Name of the file to upload
        :type filename: str
        :param test_data: Test data to upload
        :type test_data: dict
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_calculate_greeks(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch calculate greeks function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-positional-arguments
    # pylint: disable=invalid-name
    async def calculate_greeks(
        self, s0, k, r, sigma, q, T, price, option_side=None, option_type=None, **kwargs
    ):
        """
        Calculate greeks function

        :param s0: Initial price
        :type s0: float
        :param k: Strike price
        :type k: float
        :param r: Risk-free rate
        :type r: float
        :param sigma: Volatility
        :type sigma: float
        :param q: Dividend yield
        :type q: float
        :param T: Time to maturity
        :type T: float
        :param price: Price of the option
        :type price: float
        :param option_side: Side of the option (i.e. call or put)
        :type option_side: Optional[str]
        :param option_type: Type of the option (i.e. european or american)
        :type option_type: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_get_security_reference_data(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch get security reference data function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-positional-arguments
    async def get_security_reference_data(
        self,
        security_id,
        as_of_date=None,
        price=100.0,
        price_as_yield=False,
        include_schedule=False,
        use_test_data=False,
        **kwargs,
    ):
        """
        Get security reference data function

        :param security_id: Security ID
        :type security_id: str
        :param as_of_date: Date to get security reference data for
        :type as_of_date: Optional[str]
        :param price: Price of the security
        :type price: Optional[float]
        :param price_as_yield: Price as yield
        :type price_as_yield: Optional[bool | str]
        :param include_schedule: Include schedule data
        :type include_schedule: Optional[bool]
        :param use_test_data: Use test data
        :type use_test_data: Optional[bool]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_get_security_cpr(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch get security CPR function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    async def get_security_cpr(
        self, security_id, as_of_date=None, price=100.0, **kwargs
    ):
        """
        Get security CPR function

        :param security_id: Security ID
        :type security_id: str
        :param as_of_date: Date to get security CPR for
        :type as_of_date: Optional[str]
        :param price: Price of the security
        :type price: Optional[float]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_get_security_cash_flows(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch get security cash flows function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    async def get_security_cash_flows(
        self,
        security_id,
        as_of_date=None,
        price=100.0,
        lognormal=False,
        volatility=1.0,
        drift_a=1.0,
        yield_shift=100.0,
        shock_in_bp=0.0,
        price_as_yield=False,
        cpr=-9999.0,
        psa=-9999.0,
        use_test_data=False,
        **kwargs,
    ):
        """
        Get security cash flows function

        :param security_id: Security ID
        :type security_id: str
        :param as_of_date: Date to get security cash flows for
        :type as_of_date: Optional[str]
        :param price: Price of the security
        :type price: Optional[float]
        :param lognormal: Lognormal distribution
        :type lognormal: Optional[bool]
        :param volatility: Volatility
        :type volatility: Optional[float]
        :param drift_a: Mean Reversion
        :type drift_a: Optional[float]
        :param yield_shift: Yield shift
        :type yield_shift: Optional[float]
        :param shock_in_bp: Shock in basis points
        :type shock_in_bp: Optional[float]
        :param price_as_yield: Price as yield
        :type price_as_yield: Optional[bool | str]
        :param cpr: CPR
        :type cpr: Optional[float]
        :param psa: PSA
        :type psa: Optional[float]
        :param use_test_data: Use test data
        :type use_test_data: Optional[bool]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_calculate_security_analytics(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch calculate security analytics function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    async def calculate_security_analytics(
        self,
        security_id,
        as_of_date=None,
        price=100.0,
        lognormal=False,
        volatility=1.0,
        drift_a=1.0,
        yield_shift=100.0,
        shock_in_bp=0.0,
        price_as_yield=False,
        cpr=-9999.0,
        psa=-9999.0,
        use_test_data=False,
        **kwargs,
    ):
        """
        Calculate security analytics function

        :param security_id: Security ID
        :type security_id: str
        :param as_of_date: Date to calculate security analytics for
        :type as_of_date: Optional[str]
        :param price: Price of the security
        :type price: Optional[float]
        :param lognormal: Lognormal distribution
        :type lognormal: Optional[bool]
        :param volatility: Volatility
        :type volatility: Optional[float]
        :param drift_a: Mean Reversion
        :type drift_a: Optional[float]
        :param yield_shift: Yield shift
        :type yield_shift: Optional[float]
        :param shock_in_bp: Shock in basis points
        :type shock_in_bp: Optional[float]
        :param price_as_yield: Price as yield
        :type price_as_yield: Optional[bool | str]
        :param cpr: CPR
        :type cpr: Optional[float]
        :param psa: PSA
        :type psa: Optional[float]
        :param use_test_data: Use test data
        :type use_test_data: Optional[bool]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    async def batch_calculate_security_key_rates(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch calculate security key rates function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-arguments
    # pylint: disable=too-many-positional-arguments
    async def calculate_security_key_rates(
        self,
        security_id,
        as_of_date=None,
        price=100.0,
        lognormal=False,
        volatility=1.0,
        drift_a=1.0,
        yield_shift=100.0,
        key_rate_times=None,
        price_as_yield=False,
        cpr=-9999.0,
        psa=-9999.0,
        use_test_data=False,
        **kwargs,
    ):
        """
        Calculate security key rates function

        :param security_id: Security ID
        :type security_id: str
        :param as_of_date: Date to calculate security key rates for
        :type as_of_date: Optional[str]
        :param price: Price of the security
        :type price: Optional[float]
        :param lognormal: Lognormal distribution
        :type lognormal: Optional[bool]
        :param volatility: Volatility
        :type volatility: Optional[float]
        :param drift_a: Mean Reversion
        :type drift_a: Optional[float]
        :param yield_shift: Yield shift
        :type yield_shift: Optional[float]
        :param key_rate_times: Key rate times
        :type key_rate_times: Optional[list[float]]
        :param price_as_yield: Price as yield
        :type price_as_yield: Optional[bool | str]
        :param cpr: CPR
        :type cpr: Optional[float]
        :param psa: PSA
        :type psa: Optional[float]
        :param use_test_data: Use test data
        :type use_test_data: Optional[bool]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_forecast_cf_and_prices(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch forecast cash flows and prices function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    # pylint: disable=too-many-positional-arguments
    # pylint: disable=too-many-arguments
    async def forecast_cf_and_prices(
        self,
        security_id,
        as_of_date=None,
        price=100.0,
        lognormal=False,
        volatility=1.0,
        drift_a=1.0,
        yield_shift=100.0,
        shock_in_bp=0.0,
        price_as_yield=False,
        skip_projections=True,
        is_spread_shock=False,
        reindex_frequency=None,
        cpr=-9999.0,
        psa=-9999.0,
        reporting_dates_only=False,
        post_convert_currency=None,
        use_reference_curve=False,
        use_test_data=False,
        reset_convention=None,
        alt_security_id=None,
        inflation_type=None,
        **kwargs,
    ):
        """
        Forecast cash flows and prices function

        :param security_id: Security ID
        :type security_id: str
        :param as_of_date: Date to forecast cash flows and prices for
        :type as_of_date: Optional[str]
        :param price: Price of the security
        :type price: Optional[float]
        :param lognormal: Lognormal distribution
        :type lognormal: Optional[bool]
        :param volatility: Volatility
        :type volatility: Optional[float]
        :param drift_a: Mean Reversion
        :type drift_a: Optional[float]
        :param yield_shift: Yield shift
        :type yield_shift: Optional[float]
        :param shock_in_bp: Shock in basis points
        :type shock_in_bp: Optional[float]
        :param price_as_yield: Price as yield
        :type price_as_yield: Optional[bool | str]
        :param skip_projections: Skip projections
        :type skip_projections: Optional[bool]
        :param is_spread_shock: Spread shock
        :type is_spread_shock: Optional[bool]
        :param reindex_frequency: Reindex frequency (12 = monthly)
        :type reindex_frequency: Optional[int]
        :param cpr: CPR
        :type cpr: Optional[float]
        :param psa: PSA
        :type psa: Optional[float]
        :param reporting_dates_only: Reporting dates only
        :type reporting_dates_only: Optional[bool]
        :param post_convert_currency: Post convert currency
        :type post_convert_currency: Optional[str]
        :param use_reference_curve: Use reference curve
        :type use_reference_curve: Optional[bool]
        :param use_test_data: Use test data
        :type use_test_data: Optional[bool]
        :param reset_convention: Reset convention
        :type reset_convention: Optional[str]
        :param alt_security_id: Alternative security ID
        :type alt_security_id: Optional[str]
        :param inflation_type: Inflation type
        :type inflation_type: Optional[str]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """

    @hybrid
    async def batch_register_temporary_bond(
        self, batch_params=None, input_file=None, output_file=None, **kwargs
    ):
        """
        Batch register temporary bond function

        :param batch_params: dict of batch parameters
        :type batch_params: dict
        :param input_file: string path to input file
        :type input_file: str
        :param output_file: string path to output file
        :type output_file: str
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: list[dict]
        """

    @hybrid
    async def register_temporary_bond(self, reference_data, schedule_data, **kwargs):
        """
        Register temporary bond function

        :param reference_data: Reference data
        :type reference_data: dict
        :param schedule_data: Schedule data
        :type schedule_data: dict
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Results from the API
        :rtype: dict
        """
