from __future__ import annotations

import inspect
import re
from itertools import chain
from typing import Hashable, Any, Optional, Iterable, Iterator, TypeVar, get_args, cast
from uuid import UUID

from notion_df.util.exception import NotionDfValueError


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


Type_T = TypeVar('Type_T', bound=type)


def get_generic_element_type(cls: type, cast_type: Optional[Type_T] = None,
                             default_type: Optional[Type_T] = None) -> Type_T:
    """ex) class A(list[int]) -> return <class 'int'>.
    if default_type is None, non-abstract cls with non-class element type will raise ValueError."""
    try:
        generic_class = cls.__orig_bases__[0]  # type: ignore
        element_type = get_args(generic_class)[0]
        if not inspect.isabstract(cls) and isinstance(element_type, TypeVar):
            raise ValueError
        return cast(cast_type, element_type) if cast_type else element_type
    except (AttributeError, IndexError, ValueError):
        if default_type is None:
            raise NotionDfValueError('The generic class be defined with explicit element type (not TypeVar)',
                                     {'cls': cls})
        return default_type


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
