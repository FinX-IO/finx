#! python
"""
author: dick mule
purpose: utils for running async tasks and gathering results
"""
from dataclasses import dataclass, field
from typing import Any, Union
from uuid import uuid4

import asyncio
import multiprocessing as mp

import pandas as pd

from finx.utils.concurrency import Awaitable
from finx.utils.enums import ComparatorEnum

from finx.utils.concurrency import Hybrid, hybrid, ProcessWithReturnValue


NUM_CORES = mp.cpu_count()


@dataclass
class ProgressManager:
    # pylint: disable=too-many-instance-attributes
    """Manage progress updates for tasks"""
    progress: float = 0.0
    progress_scale: float = 1.0
    progress_offset: float = 0.0
    wait_time: float = 0.0
    task_name: str = None
    message: dict[str, Any] = field(default_factory=dict)
    send_messages: bool = True
    __cached_message: dict[str, Any] = field(default_factory=dict)
    # consumer: websocket

    def __post_init__(self):
        """
        Post init method for ProgressManager

        :return: None type object
        :rtype: None
        """
        self.task_name = self.task_name or f"async_task_batch_{uuid4()}"

    @staticmethod
    def chunk_progress(i: int, chunk_size: int):
        """
        utility function for determining progress message increments

        :param i: Ith task
        :type i: int
        :param chunk_size: size of chunk
        :type chunk_size: int
        :return: chunk size or 1
        :rtype: int
        """
        return int(not bool(i % chunk_size) or i == 1) * chunk_size

    def update_progress(self, n_completed: int, total_tasks: int):
        """
        Method to update progress state

        :param n_completed: Number of tasks completed
        :type n_completed: int
        :param total_tasks: Total number of tasks
        :type total_tasks: int
        :return: None type object
        :rtype: None
        """
        self.progress = n_completed / total_tasks
        self.message.update(
            progress=self.progress,
            total_tasks=total_tasks,
            remaining_tasks=f"{total_tasks - n_completed}",
            task_name=self.task_name or "",
        )

    def log_progress(self):
        """
        Method to send progress state.  Extend from stdout to websockets, etc.

        :return: None type object
        :rtype: None
        """
        if self.send_messages and self.__cached_message.get(
            "remaining_tasks"
        ) != self.message.get("remaining_tasks"):
            print(f"{self.message}")
            self.__cached_message = self.message.copy()


@dataclass(kw_only=True)
class AsyncTaskManager(ProgressManager):
    """Class to manage running of multiple coroutines"""

    tasks: list[Awaitable] = field(default_factory=list)
    chunk_size: int = -1
    __total_tasks: int = -1

    def __post_init__(self):
        """
        Post init method for AsyncTaskManager.  Wrap tasks and set chunk size

        :return: None type object
        :rtype: None
        """
        self.tasks = self.wrap_tasks(self.tasks)
        if self.chunk_size <= 0:
            self.chunk_size = len(self)
        super().__post_init__()
        self.message = self.message | {
            "total_tasks": f"{self.n_tasks}",
            "remaining_tasks": f"{self.n_tasks}",
        }

    def __len__(self):
        """
        Return length of tasks

        :return: length of tasks
        :rtype: int
        """
        return len(self.tasks)

    @property
    def n_tasks(self):
        """
        Return n tasks to be run

        :return: number of tasks
        :rtype: int
        """
        if self.__total_tasks <= 0:
            self.__total_tasks = len(self)
        return self.__total_tasks

    @n_tasks.setter
    def n_tasks(self, value: int):
        """
        Set n tasks to be run

        :param value: number of tasks
        :type value: int
        :return: None type object
        :rtype: None
        """
        self.__total_tasks = value

    @staticmethod
    async def wrap_task(async_task: Awaitable, task_id: int) -> dict:
        """
        Wraps an async task and makes it possible to retrieve results in order

        :param async_task: Awaitable async task to be wrapped
        :type async_task: Awaitable
        :param task_id: Task id
        :type task_id: int
        :return: dict of task id and result allows for sorting
        :rtype: dict
        """
        result = await async_task
        return {"id": task_id, "result": result}

    @staticmethod
    def wrap_tasks(tasks: list[Awaitable]) -> list[Awaitable]:
        """
        Wrap all tasks for sort ordering results based on original position

        :param tasks: list of tasks
        :type tasks: list[Awaitable]
        :return: list of wrapped tasks
        :rtype: list[Awaitable]
        """
        return [AsyncTaskManager.wrap_task(x, i) for i, x in enumerate(tasks)]

    @staticmethod
    def unpack_tasks(results) -> list:
        """
        Unwrap all tasks for sort ordering results based on original position

        :param results: list of dict
        :type results: list
        :return: list of results
        :rtype: list
        """
        return list(
            map(
                lambda x: x.get("result", x),
                sorted(results, key=lambda x: x.get("id", f"{uuid4()}")),
            )
        )

    @hybrid
    async def run_and_monitor(self) -> list[Any]:
        """
        Run a list of async tasks and track the progress with logging functionality

        :return: list of results
        :rtype: list
        """
        results = []
        completed = 0
        for chunk in range(1 + self.n_tasks // self.chunk_size):
            results += await asyncio.gather(
                *self.tasks[chunk * self.chunk_size : (chunk + 1) * self.chunk_size]
            )
            completed += self.chunk_size
            self.update_progress(completed, self.n_tasks)
            if self.wait_time > 0.0:
                await asyncio.sleep(self.wait_time)
        return list(
            map(
                lambda x: x.get("result", x),
                sorted(results, key=lambda x: x.get("id", f"{uuid4()}")),
            )
        )


@dataclass(kw_only=True)
class AsyncProcessManager(AsyncTaskManager):
    """Interface for running Multiprocessing tasks"""

    tasks: list[ProcessWithReturnValue] = field(default_factory=list)

    def __post_init__(self):
        """
        Post init method for AsyncProcessManager

        :return: None type object
        :rtype: None
        """
        super().__post_init__()
        self.n_tasks = len(self.tasks)

    @classmethod
    def from_args_list(
        cls, process_fn: callable, args_list: list[Any], **kwargs
    ) -> "AsyncProcessManager":
        """
        Create cls from args list

        :param process_fn: Function to be run in multiprocessing
        :type process_fn: callable
        :param args_list: List of arguments to be passed to process_fn
        :type args_list: list[Any]
        :param kwargs: Keyword arguments to be passed to process_fn
        :type kwargs: dict
        :return: AsyncProcessManager object
        :rtype: AsyncProcessManager
        """
        return cls(
            tasks=[
                ProcessWithReturnValue(process_fn, args=x, kwargs=kwargs)
                for x in args_list
            ]
        )

    @hybrid
    async def run_and_monitor(self, sleep_time: float = 0.05, **kwargs) -> list[Any]:
        """
        Run process threads limited by CPU_COUNT

        :param sleep_time: Time to sleep between checks
        :type sleep_time: float
        :param kwargs: Keyword arguments
        :type kwargs: dict
        :return: list of results
        :rtype: list
        """
        i = 0
        results = []
        while i * NUM_CORES < self.n_tasks:
            print(
                f"RUNNING AND MONITORING CHUNK = {i * NUM_CORES}:{(i + 1)* NUM_CORES}",
                end="\r",
            )
            chunked_tasks = self.tasks[i * NUM_CORES : (i + 1) * NUM_CORES]
            for task in chunked_tasks:
                task.start()
                # print(f'\tSTARTED {task}')
            if kwargs.get("start_only"):
                continue
            # print(f'\tJOINING {chunked_tasks}')
            results += [await thread.join_async(sleep_time) for thread in chunked_tasks]
            i += 1
        print("Finished running processes")
        return results


class ConcurrencyTypes(ComparatorEnum):
    """Enumerate various concurrency methods"""

    async_thread = 1
    async_process = 2

    @staticmethod
    def as_str(_type: "ConcurrencyTypes") -> str:
        """
        Get enum value str from type

        :param _type: Enum type
        :type _type: ConcurrencyTypes
        :return: Enum value as string
        :rtype: str
        """
        return ConcurrencyTypes.list()[int(_type) - 1]


@dataclass(kw_only=True)
class TaskRunner(AsyncProcessManager):
    """Interface for running a variety of async methods"""

    async_func: Union[ProcessWithReturnValue, Hybrid]
    tasks: list[Awaitable | ProcessWithReturnValue] = field(default_factory=list)
    concurrency_type: str | ConcurrencyTypes = field(
        default_factory=lambda: ConcurrencyTypes.async_thread
    )

    def __post_init__(self):
        """
        Post init method for TaskRunner

        :return: None type object
        :rtype: None
        """
        if isinstance(self.concurrency_type, str):
            self.concurrency_type = ConcurrencyTypes.get(
                self.concurrency_type, default="async_thread"
            )
        super().__post_init__()
        self.tasks = [self.runnable] * self.n_tasks

    @staticmethod
    def _coerce_args(args_list: Any) -> list[Any]:
        """
        utility function for parsing/formatting arguments passed to run_concurrently

        :param args_list: List of arguments to be coerced
        :type args_list: Any
        :return: List of arguments
        :rtype: list[Any]
        """
        input_type = type(args_list)
        if input_type is list:
            return args_list
        if input_type is pd.Series:
            return args_list.tolist()
        if input_type is pd.DataFrame:
            return args_list.to_dict(orient="records")
        if input_type is dict:
            return list(args_list.items())
        raise ValueError(f"Cannot cast {input_type} to list")

    @property
    def runnable(self):
        """
        Return async function to call

        :return: Async function to call
        :rtype: Union[CeleryWrapper, Hybrid]
        """
        if self.concurrency_type is ConcurrencyTypes.async_process:
            return self.async_func
        return self.async_func

    @hybrid
    async def _run_async_process(
        self, args_list: list[Any], no_return: bool = False, **kwargs
    ):
        """
        Specify that we are running async process tasks

        :param args_list: List of arguments to be passed to async function
        :type args_list: list[Any]
        :param no_return: Flag to determine if we are running in sync context
        :type no_return: bool
        :param kwargs: Keyword arguments to be passed to async function
        :type kwargs: dict
        :return: None type object
        :rtype: None
        """
        print(f"RUN ASYNC PROCESS: {no_return=}")
        self.tasks = [
            self.async_func(**args_list[i], no_return=no_return, **kwargs)
            for i in range(self.n_tasks)
        ]
        return await AsyncProcessManager.run_and_monitor(self)

    @hybrid
    async def _run_async_thread(self, args_list: list[Any], **kwargs):
        """
        Specify that we are running async hybrid tasks

        :param args_list: List of arguments to be passed to async function
        :type args_list: list[Any]
        :param kwargs: Keyword arguments to be passed to async function
        :type kwargs: dict
        :return: None type object
        :rtype: None
        """
        self.tasks = self.wrap_tasks(
            [self.async_func(args_list[i], **kwargs) for i in range(self.n_tasks)]
        )
        return await AsyncTaskManager.run_and_monitor(self)

    @hybrid
    async def run_concurrently(self, args_list: list[Any], **kwargs) -> list[Any]:
        """
        Utility function for running parallel tasks and aggregating result

        :param args_list: List of arguments to be passed to async function
        :type args_list: list[Any]
        :param kwargs: Keyword arguments to be passed to async function
        :type kwargs: dict
        :return: list of results
        :rtype: list
        """
        if kwargs.pop("coerce", True):
            args_list = self._coerce_args(args_list)
        self.n_tasks = len(args_list)
        self.chunk_size = self.chunk_size or self.n_tasks
        return await getattr(
            self, f"_run_{ConcurrencyTypes.as_str(self.concurrency_type)}"
        )(args_list, **kwargs)
