#! python
"""
author: dick mule
purpose: FinX Rest Client
"""
from typing import Any
from platform import system

import json

import requests

from finx.base_classes.base_client import BaseFinXClient, SessionManager
from finx.base_classes.context_manager import CacheLookup
from finx.utils.concurrency import hybrid
from finx.utils.task_runner import TaskRunner


# pylint: disable=no-member
# pylint: disable=consider-using-with)
# pylint: disable=missing-timeout


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
        # pylint: disable=useless-parent-delegation
        super().model_post_init(__context)

    async def __aenter__(self) -> "FinXRestClient":
        await self.load_functions()
        return self

    async def __aexit__(self, *err) -> None:
        self.cleanup()

    def _unpack_session_response(self, data: dict, cache_lookup: CacheLookup) -> dict:
        """

        :param data: Dict of data from the API
        :type data: dict
        :param cache_lookup: Cache lookup object
        :type cache_lookup: CacheLookup
        :return: Data from the API
        :rtype: dict
        """
        if (error := data.get("error")) is not None:
            print(f"API returned error: {error}")
            return error
        if isinstance(data.get("data"), dict) and data.get("data", {}).get("filename"):
            data = self.download_file(data["data"])
        self.context.cache[cache_lookup.key] = data
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
        payload: dict = {"finx_api_key": self.context.api_key, "api_method": api_method}
        is_json_data = len(kwargs) > 0
        payload.update(
            {
                key: value
                for key, value in kwargs.items()
                if key not in ["finx_api_key", "api_method"]
            }
        )
        cache_lookup = self.context.check_cache(api_method, **kwargs)
        if cache_lookup.value is not None:
            return cache_lookup.value
        print(f"API CALL: {api_method} with {payload} / {kwargs}")
        if not self.session:
            async with SessionManager() as session:
                data = await session.post(
                    self.context.api_url, is_json_data=is_json_data, **payload
                )
                return self._unpack_session_response(data, cache_lookup)
        data = await self.session.post(
            self.context.api_url, is_json_data=is_json_data, **payload
        )
        return self._unpack_session_response(data, cache_lookup)

    @hybrid
    async def _batch_dispatch(
        self, api_method: str, batch_params: list[dict], **kwargs
    ) -> list[dict]:
        """
        Abstract batch request dispatch function. Issues a request for each input

        :param api_method: API method to call
        :type api_method: str
        :param batch_params: List of api method parameters
        :type batch_params: list[dict]
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: Response from the API
        :rtype: list[dict]
        """
        assert (
            api_method != "list_api_functions"
            and isinstance(batch_params, list)
            and len(batch_params) < 100
        )
        runner = TaskRunner(async_func=self._dispatch, concurrency_type="async")
        return runner.run_concurrently(
            [{"api_method": api_method} | params for params in batch_params], **kwargs
        )

    @property
    def rest_url(self):
        """
        Get the websocket URL

        :return: Websocket URL
        :rtype: str
        """
        return self.context.api_url.replace("/api/", "/cms2/")

    @staticmethod
    def _file_delim():
        file_delim = "/"
        if system().lower() == "windows":
            file_delim = "\\"
        return file_delim

    def import_private_data(self, full_file_path: str) -> bool:
        """
        Import private data

        :param full_file_path: Full path to FinX private data template (i.e. /full/path/to/file.xlsx)
        :type full_file_path: str
        :return: True if successful
        :rtype: bool
        """
        response = requests.post(
            f"{self.rest_url}upload_private_data/",
            files={"file": open(full_file_path, "rb")},
            data={
                "user_uuid": self.context.api_key,
                "filename": full_file_path.split(self._file_delim)[-1],
                "test_data": True,
            },
        )
        return response.status_code == 200

    def submit_batch_run(self, full_file_path: str) -> str:
        """
        Submit a batch run using the xlsx input configuration file

        :param full_file_path: Full path to the batch run file
        :type full_file_path: str
        :return: Task ID to monitor
        :rtype: str
        """
        response = requests.post(
            f"{self.rest_url}submit_batch_run/",
            files={"file": open(full_file_path, "rb")},
            data={
                "user_uuid": self.context.api_key,
                "source_file": full_file_path.split(self._file_delim)[-1],
            },
        )
        if response.status_code == 200:
            return response.json()["task"]
        raise ValueError(f"Error submitting batch run for {full_file_path}")

    def monitor_progress(self, task_id: str) -> dict:
        """
        Monitor the progress of a batch run

        :param task_id: Task ID to monitor
        :type task_id: str
        :return: Progress of the task
        :rtype: dict
        """
        response = requests.get(
            f"{self.rest_url}monitor_batch_progress/",
            params={"task_id": task_id, "user_uuid": self.context.api_key},
        )
        return response.json()

    def get_file_result(self, task_id: str) -> bool:
        """
        Get the result of a batch run

        :param task_id: Task ID to monitor
        :type task_id: str
        :return: Progress of the task
        """
        status = self.monitor_progress(task_id)
        if status["total_status"] != "complete":
            return False
        for subtask_id, task_results in status["subtask_status"].items():
            filename = task_results["download_file"]
            print(f"downloading file for {subtask_id=} => {filename} ...")
            response = requests.get(
                f"{self.rest_url}download_file/", params={"filename": filename}
            )
            with open(filename, "wb") as f:
                f.write(response.content)
        return True

    def register_scenario_rates(self, rates_filename: str) -> dict:
        """
        Register scenario rates

        :param rates_filename: Filename of the rates file
        :type rates_filename: str
        :return: Response from the API
        :rtype: dict
        """
        response = requests.get(
            f"{self.rest_url}register_batch_file/",
            params={"user_uuid": self.context.api_key, "filename": rates_filename},
        )
        return response.json()

    def run_batch_holdings(self, path_to_holdings_file: str, tasks_to_run: dict) -> str:
        """
        Run a batch job for a given set of holdings in a .csv file and specify what task configurations to run.

        :param path_to_holdings_file: Path to the holdings file
        :type path_to_holdings_file: str
        :param tasks_to_run: Tasks to run in the batch job
        :type tasks_to_run: dict
        :return: Task ID to monitor
        :rtype: str
        """
        response = requests.post(
            f"{self.rest_url}submit_batch_file/",
            files={"file": open(path_to_holdings_file, "rb")},
            data={
                "user_uuid": self.context.api_key,
                "filename": path_to_holdings_file.split(self._file_delim())[-1],
                "tasks_to_run": json.dumps(tasks_to_run),
            },
        ).json()
        return response
