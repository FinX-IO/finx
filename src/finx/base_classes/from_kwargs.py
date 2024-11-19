"""
author: dick mule
purpose: interface to create class from Kwargs
"""

from inspect import signature
from typing import Any

from pydantic import BaseModel

from finx.utils.concurrency import Hybrid


# pylint: disable=too-few-public-methods
class BaseMethods(BaseModel):
    """Base method expanding pydantic model to be initialized from dict with extra values"""

    extra_attrs: dict[Any, Any] = {}

    class Config:
        """Nested Config for Pydantic Model"""

        arbitrary_types_allowed = True
        ignored_types = (Hybrid,)

    def model_post_init(self, __context: Any) -> None:
        """
        Pydantic model post init method to set up the c++ library

        :param __context: A context dictionary for the model
        :type __context: dict
        :return: None type object
        :rtype: None
        """
        # pylint: disable=useless-parent-delegation
        super().model_post_init(__context)

    @classmethod
    def from_kwargs(cls, **kwargs) -> "BaseMethods":
        """
        Construct any base class from kwargs regardless of whether they're part of the class

        :param kwargs: dictionary of all initialization values
        :type kwargs: dict
        :return: instance of the class
        :rtype: cls
        """
        native_args, new_args = {}, {}
        cls_fields = set(signature(cls).parameters)
        for name, val in kwargs.items():
            if name in cls_fields:
                native_args[name] = val
            else:
                new_args[name] = val
        ret = cls(**native_args)
        for new_name, new_val in new_args.items():
            ret.extra_attrs[new_name] = new_val
        return ret
