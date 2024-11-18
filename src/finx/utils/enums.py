#! python
"""
author: dick mule
purpose: extend enum class
"""
from dataclasses import field
from itertools import count
from typing import Any

from aenum import Enum, NoAlias


class EnumFunction:
    """Class for enum values.  Useful for assigning callable values to enums."""

    def __init__(self, function: callable):
        """
        Wrap function and make it available to enum.

        :param function: Function to assign to enum
        :type function: callable
        """
        self.function = function

    def __call__(self, *args, **kwargs):
        return self.function(*args, **kwargs)


class ExtendedEnum(Enum):
    """Enum extended with useful methods."""

    @classmethod
    def fromlist(cls, classname: str, data: list[dict], enum_key: str):
        """
        Create enum from list of dictionaries

        :param classname: create enum with this name
        :type classname: str
        :param data: list of dictionaries
        :type data: list[dict]
        :param enum_key: key to use for enum value
        :type enum_key: str
        :return: Enum class
        :rtype: Enum
        """
        return cls(classname, [(f"{x[enum_key]}", x) for x in data])

    @classmethod
    def list(cls, name: bool = True) -> list:
        """
        Return list of enum values

        :param name: return name if True, otherwise return value
        :type name: bool
        :return: list of enum values
        :rtype: list
        """
        return list(map(lambda c: (name and c.name) or c.value, cls))

    @classmethod
    def tuple(cls, name: bool = True) -> tuple:
        """
        Return tuple of enum values

        :param name: return name if True, otherwise return value
        :type name: bool
        :return: tuple of enum values
        :rtype: tuple
        """
        return tuple(cls.list(name))

    @classmethod
    def dict(cls) -> dict:
        """
        Return dictionary of enum values

        :return: dictionary of enum values
        :rtype: dict
        """
        return dict(map(lambda c: (c.name, c.value), cls))

    @classmethod
    def get(cls, key: str, default: str = None, default_return: Any = None):
        """
        Get enum value by key

        :param key: enum value name
        :type key: str
        :param default: default value to return if key not found
        :type default: str
        :param default_return: default value to return if key not found
        :type default_return: Any
        :return: enum value
        :rtype: Any
        """
        self_as_dict = cls.dict()
        value = self_as_dict.get(key)
        if value is not None:
            return value
        if default:
            try:
                return self_as_dict[default]
            except KeyError:
                pass
        if default_return is not None:
            return default_return
        raise KeyError(
            f"Invalid field ({key=}) for {cls}, please choose from one of the following: {cls.list()}"
        )


class NoAliasEnum(ExtendedEnum):
    """Enum with no alias"""

    _settings_ = NoAlias


class ComparatorEnum(ExtendedEnum):
    """Enum with comparison methods"""

    def __int__(self):
        """
        Return enum value as integer

        :return: enum value as integer
        :rtype: int
        """
        return self.value

    def __hash__(self):
        return int(self)

    def __valid_comparison(self, other) -> bool:
        """
        Check if comparison is valid

        :param other: other value to compare
        :type other: int | self.__class__
        :return: True if comparison is valid, otherwise False
        :rtype: bool
        """
        return any(other.__class__ is x for x in [self.__class__, int])

    def __lt__(self, other):
        """
        Less than comparison

        :param other: other value to compare
        :type other: int | self.__class__
        :return: True if less than, otherwise False
        :rtype: bool
        """
        if self.__valid_comparison(other):
            other_value = getattr(other, "value", other)
            return self.value < other_value
        return NotImplemented

    def __le__(self, other):
        """
        Less than or equal comparison

        :param other: other value to compare
        :type other: int | self.__class__
        :return: True if less than or equal, otherwise False
        :rtype: bool
        """
        if self.__valid_comparison(other):
            other_value = getattr(other, "value", other)
            return self.value <= other_value
        return NotImplemented

    def __gt__(self, other):
        """
        Greater than comparison

        :param other: other value to compare
        :type other: int | self.__class__
        :return: True if greater than, otherwise False
        :rtype: bool
        """
        if self.__valid_comparison(other):
            other_value = getattr(other, "value", other)
            return self.value > other_value
        return NotImplemented

    def __ge__(self, other):
        """
        Greater than or equal comparison

        :param other: other value to compare
        :type other: int | self.__class__
        :return: True if greater than or equal, otherwise False
        :rtype: bool
        """
        if self.__valid_comparison(other):
            other_value = getattr(other, "value", other)
            return self.value >= other_value
        return NotImplemented

    def __eq__(self, other):
        """
        Equal comparison

        :param other: other value to compare
        :type other: int | self.__class__
        :return: True if equal, otherwise False
        :rtype: bool
        """
        if self.__valid_comparison(other):
            other_value = getattr(other, "value", other)
            return self.value == other_value
        return NotImplemented
