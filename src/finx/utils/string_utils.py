#! python
"""
author: dick mule
purpose: utils for handling c++ strings
"""
import re


def camel_to_snake(x: str) -> str:
    """
    Convert camelCaseString to snake_case_string

    :param x: any string
    :type x: str
    :return: snake_case_string
    :rtype: str
    """
    matched = re.sub("([A-Z]+)", r"_\1", f"{x}").lower()
    return (matched.split("_")[0] and matched) or matched.replace("_", "")
