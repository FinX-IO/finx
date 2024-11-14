#! python
"""
author: dick mule
purpose: utils for parsing payloads - sizing/etc.
"""
from sys import getsizeof
from typing import Any


def get_size(obj: Any, seen: set = None) -> int:
    """
    Recursively finds size of objects

    :param obj: Any PyObject
    :type obj: Any
    :param seen: Set of objects seen
    :type seen: set
    :return: Size of object
    :rtype: int
    """
    size = getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size
