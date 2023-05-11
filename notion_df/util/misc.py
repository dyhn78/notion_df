from __future__ import annotations

import inspect
import re
from itertools import chain
from typing import Hashable, Any, Optional, Iterable, Iterator, TypeVar, get_args, cast, Generic, get_type_hints
from uuid import UUID

from notion_df.util.exception import NotionDfTypeError


def repr_object(obj: Any, params: dict[Hashable, Any] = None, **kwargs: Any) -> str:
    # TODO: replace this with `dataclass.field(repr: bool)` feature
    """params and kwargs has same effect"""
    items = _concat_items(params, kwargs)
    return f"{type(obj).__name__}({', '.join(f'{k}={v}' for k, v in items if v is not None)})"


def _concat_items(params: Optional[dict[Hashable, Any]], kwargs: dict[str, Any]) -> Iterable[tuple[Hashable, str]]:
    return chain(params.items() if params is not None else (), kwargs.items())  # type: ignore


def get_num_iterator() -> Iterator[int]:
    num = 0
    while True:
        yield num
        num += 1


uuid_pattern = re.compile(r'[0-9a-f]{8}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{4}-?[0-9a-f]{12}', re.I)


def get_id(id_or_url: str | UUID) -> UUID:
    # Regular expression to match both dashed and no-dash UUIDs
    if isinstance(id_or_url, UUID):
        return id_or_url
    match = uuid_pattern.search(id_or_url)
    if match:
        return UUID(match.group(0))
    else:
        return UUID(id_or_url)


Type_T = TypeVar('Type_T', bound=type)


def get_generic_args(cls: type[Generic]) -> Optional[tuple[type, ...]]:
    """ex) class A(list[int]) -> return (<class 'int'>,)."""
    for base in cls.__orig_bases__:
        if args := get_args(base):
            return args


def get_generic_arg(cls: type[Generic], cast_type: Type_T) -> Type_T:
    """ex) class A(list[int]) -> return: <class 'int'>"""
    try:
        arg = cast(type[cast_type], get_generic_args(cls)[0])
    except IndexError:
        raise NotionDfTypeError(f'{cls.__name__} should be explicitly subscribed')
    if not inspect.isabstract(cls) and not inspect.isclass(arg):
        raise NotionDfTypeError(
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
        raise NotionDfTypeError('all class attributes must be filled',
                                {'cls': cls, 'undefined_attr_names': attr_names})
