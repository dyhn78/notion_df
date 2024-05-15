from __future__ import annotations

import inspect
from typing import TypeVar, Generic, Optional, get_args, cast, get_type_hints, Any


class _Undefined:
    def __repr__(self) -> str:
        return "Undefined"


undefined = _Undefined()


def repr_object(obj, *attrs: Any, **kw_attrs: Any) -> str:
    def _repr(_attr_value): return repr(_attr_value) if isinstance(_attr_value, str) else str(_attr_value)

    attr_items = []
    for attr_value in attrs:
        if attr_value is undefined:
            continue
        attr_items.append(_repr(attr_value))
    for attr_name, attr_value in kw_attrs.items():
        if attr_value is undefined:
            continue
        attr_items.append(f'{attr_name}={_repr(attr_value)}')
    return f"{type(obj).__name__}({', '.join(attr_items)})"


TypeT = TypeVar('TypeT', bound=type)


def get_generic_args(cls: type[Generic]) -> Optional[tuple[type, ...]]:
    """ex) class A(list[int]) -> return (<class 'int'>,)."""
    for base in cls.__orig_bases__:
        if args := get_args(base):
            return args


def get_generic_arg(cls: type[Generic], cast_type: TypeT) -> TypeT:
    """ex) class A(list[int]) -> return: <class 'int'>"""
    try:
        arg = cast(type[cast_type], get_generic_args(cls)[0])
    except IndexError:
        raise TypeError(f'{cls.__name__} should be explicitly subscribed')
    if not inspect.isabstract(cls) and not inspect.isclass(arg):
        raise TypeError(
            f'since {cls.__name__} is not abstract, it should be subscribed with class arguments (not TypeVar)')
    return arg


def check_classvars_are_defined(cls):
    if inspect.isabstract(cls):
        return
    attr_names = []
    for attr_name, attr_type in get_type_hints(cls).items():
        if hasattr(super(cls), attr_name) and not hasattr(cls, attr_name):
            attr_names.append(attr_name)
    if attr_names:
        raise TypeError('all class attributes must be filled', {'cls': cls, 'undefined_attr_names': attr_names})
