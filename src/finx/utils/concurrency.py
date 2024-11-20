#! python
"""
author: dick mule
purpose: utils for facilitating concurrency of methods
"""
from typing import Any, Callable, Coroutine, Union

import asyncio
import functools
import multiprocessing as mp
import threading

from asgiref.sync import sync_to_async, async_to_sync
import nest_asyncio

Awaitable = Union[asyncio.Task, Coroutine]
_ALREADY_RUNNING = asyncio.get_event_loop().is_running()


def decohints(decorator: Callable) -> Callable:
    """
    Decorator allowing better type hints for class decorators.

    :param decorator: Callable Decorator Class
    :type decorator: Callable
    :return: Wrapped Callable object
    :rtype: Callable
    """
    return decorator


def to_async(func: Callable, thread_safe: bool = False):
    """
    Wrap asgiref functionality.  Easier naming convention.

    :param func: Sync method to be converted to async.
    :type func: Callable
    :param thread_safe: Specify whether to make thread safe
    :type thread_safe: bool
    :return: Converted Sync method -> Coroutine
    :rtype: Coroutine
    """
    return sync_to_async(func, thread_sensitive=thread_safe)


def to_sync(func: Awaitable, force_new_loop: bool = False):
    """
    Wrap asgiref functionality.  Easier naming convention.

    :param func: Async method to be converted to sync.
    :type func: Awaitable
    :param force_new_loop: Specify whether to force new loop
    :type force_new_loop: bool
    :return: Converted Async method -> Sync
    :rtype: Callable
    """
    return async_to_sync(func, force_new_loop=force_new_loop)


def task_runner(task: Coroutine, loop: asyncio.AbstractEventLoop = None):
    """
    Run async task in event loop.  If loop is not running, create new loop.

    :param task: Async method to be run
    :type task: Coroutine
    :param loop: Event loop to run task
    :type loop: asyncio.AbstractEventLoop
    :return: Result of async method
    :rtype: Any
    """
    new_loop: bool = False
    if loop is None:
        try:
            loop = asyncio.get_event_loop()
        except RuntimeError:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            new_loop = True
    is_running: bool = loop.is_running()
    not_already = not _ALREADY_RUNNING
    run_loop = [loop.run_until_complete, loop.create_task][is_running and not_already]
    result = None
    try:
        result = run_loop(task)
        if new_loop and not_already:
            loop.close()
        return result
    except TypeError as exc:
        raise TypeError(f"BAD LOOP PARAMS: {task=} / {result}") from exc
    except RuntimeError:
        # catch RuntimeError: This event loop is already running -> use nest_asyncio
        # print(f"APPLY NEST ASYNCIO: {loop=} / {_ALREADY_RUNNING=}")
        nest_asyncio.apply(loop)
        try:
            result = loop.create_task(task)
            if new_loop and not_already:
                loop.close()
            return result
        except TypeError as t_exc:
            raise TypeError(f"BAD LOOP PARAMS: {task=} / {result}") from t_exc
        except RuntimeError as r_exc:
            print(f"RUNTIME ERROR: {r_exc=}")
            if f"{r_exc}" == "Event loop stopped before Future completed.":
                return result
            raise RuntimeError(f"BAD LOOP PARAMS: {task=} / {result}") from r_exc


class Hybrid:
    """Add some features to hybrid async methods"""

    def __init__(self, func: Callable | Awaitable):
        """
        Initialize Hybrid class with function

        .. code-block:: python

            @Hybrid
            async def awaitable_fn():
                await asyncio.sleep(1)
                return "done"

        :param func: Function to be wrapped
        :type func: Callable | Awaitable
        """
        self._func: Callable = func
        self._func_name: str = func.__name__
        self._func_path: str = func.__name__
        self._func_class: Any = None
        self._event_loop: asyncio.AbstractEventLoop = None
        functools.update_wrapper(self, func)

    @property
    def my_func(self):
        """
        Property returning protected _func

        :return: Function to be wrapped
        :rtype: Callable
        """
        return self._func

    def __get__(self, instance, owner):
        """
        Support class instance methods.

        :param instance: instance of the class to which the descriptor is attached
        :type instance: object
        :param owner: the class which contains the descriptor
        :type owner: type
        :return: Hybrid object
        :rtype: Hybrid
        """
        self._func_class = instance
        return self

    def __call__(self, *args, **kwargs):
        """
        Call method to run function

        :param args: All args to be passed to function
        :type args: tuple
        :param kwargs: All kwargs to be passed to function
        :type kwargs: dict
        :return: Async result of function
        :rtype: Any
        """
        return task_runner(self.run_func(*args, **kwargs), self._event_loop)

    def set_event_loop(self, loop: asyncio.AbstractEventLoop):
        """
        Set event loop for function

        :param loop: Event loop to be set
        :type loop: asyncio.AbstractEventLoop
        :return: None
        :rtype: None
        """
        self._event_loop = loop

    async def run_func(self, *args, **kwargs):
        """
        Run function async

        :param args: All args to be passed to function
        :type args: tuple
        :param kwargs: All kwargs to be passed to function
        :type kwargs: dict
        :return: Async result of function
        :rtype: Any
        """
        if self._func_class is not None:
            args = (self._func_class,) + args
        return await self._func(*args, **kwargs)

    async def run_async(self, *args, **kwargs):
        """
        Run function async.  Makes it so that an async hybrid function
        can always be specified as a coroutine for parallel tasks.

        .. code-block:: python

            tasks = [some_fn.run_async(i) for i in range(10)]
            results = await asyncio.gather(*tasks)

        :param args: All args to be passed to function
        :type args: tuple
        :param kwargs: All kwargs to be passed to function
        :type kwargs: dict
        :return: Async result of function
        :rtype: Any
        """
        return await self.run_func(*args, **kwargs)

    @property
    def func_class(self):
        """
        Property returning protected _func_class

        :return: Func class name
        :rtype: str
        """
        return self._func_class

    @property
    def func_name(self):
        """
        Property returning protected _func_name

        :return: Wrapped function name
        :rtype: str
        """
        return self._func_name

    @property
    def event_loop(self):
        """
        Property returning protected _event_loop

        :return: Event loop
        :rtype: asyncio.AbstractEventLoop
        """
        return self._event_loop


@decohints
def hybrid(f: Callable) -> Hybrid:
    """
    Decorator to make function hybrid

    .. code-block:: python

        @hybrid
        async def awaitable_fn():
            await asyncio.sleep(1)
            return "done"

        class SomeClass:
            ...

            @hybrid
            async def awaitable_fn(self):
                await asyncio.sleep(1)
                return "done"

    :param f: Function to be wrapped
    :type f: Callable
    :return: Hybrid object
    :rtype: Hybrid
    """
    return Hybrid(f)


class ThreadWithReturnValue(threading.Thread):
    """Thread class with return value"""

    # pylint: disable=too-many-positional-arguments
    # pylint: disable=too-many-function-args
    def __init__(
        self, target=None, group=None, name=None, args=(), kwargs=None, daemon=None
    ):
        """
        Initialize ThreadWithReturnValue class.
        Note from base class: If a subclass overrides the constructor, it must make sure to invoke
        the base class constructor (Thread.__init__()) before doing anything
        else to the thread.

        :param target: Callable function
        :type target: callable
        :param group: Should be None; reserved for future extension when a ThreadGroup
        class is implemented.
        :type group: None
        :param name: Is the callable object to be invoked by the run()
        method. Defaults to None, meaning nothing is called.
        :type name: str
        :param args: The arguments to be passed to the target function
        :type args: tuple
        :param kwargs: The keyword arguments to be passed to the target function
        :type kwargs: dict
        :param daemon: A boolean value indicating whether this thread is a daemon thread
        :type daemon: bool
        """
        super().__init__(self, group, target, name, args, kwargs, daemon=daemon)
        self._return = None

    def check_event_loop(self):
        """
        create new event loop within multiprocessing child process

        :return: None
        :rtype: None
        """
        if isinstance(self._target, Hybrid) or self._kwargs.pop(
            "make_event_loop", None
        ):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

    def run(self):
        """
        Override run function to execute target

        :return: Run the target function
        :rtype: Any
        """
        if self._target is not None:
            self.check_event_loop()
            self._return = self._target(*self._args, **self._kwargs)

    def join(self, *args):
        """
        Wait for process to finish and get return value

        :param args: All args for join
        :type args: tuple
        :return: Return value of target function
        :rtype: Any
        """
        super().join(self, *args)
        return self._return


class ProcessWithReturnValue(mp.Process):
    """Another processing class"""

    # pylint: disable=too-many-positional-arguments
    def __init__(
        self,
        target: Union[callable, Hybrid] = None,
        name: str = None,
        args: tuple = (),
        kwargs: dict = None,
        no_return: bool = False,
    ):
        """
        Initialize ProcessWithReturnValue class

        :param target: Callable function to be run in parallel
        :type target: Union[callable, Hybrid]
        :param name: Name of process
        :type name: str
        :param args: All args to be passed to target function
        :type args: tuple
        :param kwargs: All kwargs to be passed to target function
        :type kwargs: dict
        :param no_return:
        :type  no_return:
        """
        self._return = [mp.Queue, lambda: None][no_return]()
        self.target_to_wrap: Union[callable, Hybrid] = target
        mp.Process.__init__(self, None, self.wrap_process, name, args, kwargs or {})

    @staticmethod
    def check_event_loop():
        """
        create new event loop within multiprocessing child process

        :return: Running event loop or one created
        :rtype: asyncio.AbstractEventLoop
        """
        policy = asyncio.get_event_loop_policy()
        policy.set_event_loop(policy.new_event_loop())
        loop = asyncio.get_event_loop()
        return loop

    def wrap_process(self, *args, **kwargs):
        """
        Wrap target function

        :param args: All input arguments as tuple
        :type args: tuple
        :param kwargs: All input keyword arguments as dict
        :type kwargs: dict
        :return: None
        :rtype: None
        """
        if isinstance(self.target_to_wrap, Hybrid):
            loop = self.check_event_loop()
            result = task_runner(
                self.target_to_wrap.run_async(*args, **kwargs), self.check_event_loop()
            )
            loop.close()
        else:
            result = self.target_to_wrap(*args, **kwargs)
        if self._return is not None:
            self._return.put(result)

    def run(self):
        """
        Override run function to execute target

        :return: None
        :rtype: None
        """
        self._target(*self._args, **self._kwargs)

    def join(self, *args):
        """
        Wait for process to finish and get return value

        :param args: Tuple of input arguments
        :type args: tuple
        :return: Result of target function
        :rtype: str
        """
        mp.Process.join(self, *args)
        if self._return is None:
            return None
        result = self._return.get()
        return result

    @hybrid
    async def join_async(self, *args, sleep_time: float = 0.05):
        """
        Wait for process to finish and get return value

        :param args: Tuple of input arguments
        :type args: tuple
        :param sleep_time: Time to sleep before checking if process is alive
        :type sleep_time: float
        :return: Result of target function
        :rtype: str
        """
        while self.is_alive():
            await asyncio.sleep(sleep_time)
        mp.Process.join(self, *args)
        if self._return is None:
            return None
        result = self._return.get()
        return result


class ThreadFunction:
    """Thread function class decorator"""

    def __init__(self, thread_fn: Callable = None):
        """
        Initialize ThreadFunction class

        :param thread_fn: Function to be wrapped
        :type thread_fn: Callable
        """
        self.thread_function = thread_fn
        self._func_classes = []

    def __call__(self, *args, **kwargs):
        """
        Call method to run function

        :param args: args for wrapped function
        :type args: tuple
        :param kwargs: kwargs for wrapped function
        :type kwargs: dict
        :return: Result of wrapped function
        :rtype: Any
        """
        return self.thread_function(*args, **kwargs)

    def __get__(self, obj, objtype):
        """
        Support instance methods.

        :param obj: attribute of object
        :type obj: Any
        :param objtype: type of object
        :type objtype: Any
        :return: ThreadFunction object
        :rtype: ThreadFunction
        """
        self._func_classes += [obj]
        return self

    def check_args(self, *args):
        """
        Check if function classes are available

        :param args: All args to be passed to function
        :type args: tuple
        :return: All args to be passed to function
        :rtype: tuple
        """
        if len(self._func_classes) > 0:
            args = (self._func_classes.pop(0),) + args
        return args

    def thread(self, *args, **kwargs):
        """
        Run function as thread

        :param args: All arguments for wrapped function
        :type args: tuple
        :param kwargs: All keyword arguments for wrapped function
        :type kwargs: dict
        :return: Thread object
        :rtype: ThreadWithReturnValue
        """
        kwargs.update(make_event_loop=isinstance(self.thread_function, Hybrid))
        thread = ThreadWithReturnValue(
            target=self.thread_function, args=self.check_args(*args), kwargs=kwargs
        )
        thread.start()
        return thread

    def process(self, *args, **kwargs):
        """
        Run function as separate process

        :param args: All arguments for wrapped function
        :type args: tuple
        :param kwargs: All keyword arguments for wrapped function
        :type kwargs: dict
        :return: Process object
        :rtype: ProcessWithReturnValue
        """
        process = ProcessWithReturnValue(
            target=self.thread_function, args=self.check_args(*args), kwargs=kwargs
        )
        process.start()
        return process


@decohints
def thread_function(f: callable) -> callable:
    """
    Decorator to make function a thread function

    :param f: Function to be wrapped
    :type f: callable
    :return: ThreadFunction object
    :rtype: ThreadFunction
    """
    return ThreadFunction(f)
