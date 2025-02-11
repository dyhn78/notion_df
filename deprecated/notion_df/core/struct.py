from __future__ import annotations

import inspect
from typing import TypeVar, Generic, Optional, get_args, cast, get_type_hints, Any

TypeT = TypeVar("TypeT", bound=type)


def get_generic_args(cls: type[Generic]) -> Optional[tuple[type, ...]]:
    """ex. class A(list[int]) -> return (<class 'int'>,)."""
    for base in cls.__orig_bases__:
        if args := get_args(base):
            return args


def get_generic_arg(cls: type[Generic], cast_type: TypeT) -> TypeT:
    """ex. class A(list[int]) -> return: <class 'int'>"""
    try:
        arg = cast(type[cast_type], get_generic_args(cls)[0])
    except IndexError:
        raise TypeError(f"{cls.__name__} should be explicitly subscribed")
    if not inspect.isabstract(cls) and not inspect.isclass(arg):
        raise TypeError(
            f"since {cls.__name__} is not abstract, it should be subscribed with class arguments (not {arg})"
        )
    return arg


def check_classvars_are_defined(cls):
    if inspect.isabstract(cls):
        return
    attr_names = []
    for attr_name, attr_type in get_type_hints(cls).items():
        if hasattr(super(cls), attr_name) and not hasattr(cls, attr_name):
            attr_names.append(attr_name)
    if attr_names:
        raise TypeError(
            "all class attributes must be filled",
            {"cls": cls, "undefined_attr_names": attr_names},
        )
