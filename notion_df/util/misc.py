from __future__ import annotations

from abc import ABC
from dataclasses import dataclass, field
from itertools import chain
from typing import Hashable, Any, Optional, Iterable, Iterator

_BR = '_BR'


@dataclass
class NotionDfException(Exception, ABC):
    """the base exception class, defined with dataclass style.
    __doc__: class-level description
    description: instance-specific description
    vars: dumped variables to display in error log"""
    description: str = field()
    """instance-specific description"""
    vars: dict[str, Any] = field()
    """dumped variables in error log"""
    def __init_subclass__(cls, **kwargs):
        dataclass(cls)
        if cls.__doc__ != NotionDfException.__doc__:
            cls.__doc__ = None
        # if not isabstract(cls) and is_dataclass(cls):
        #     raise NotionDfValueError('NotionDfException must be defined as dataclass style', {'cls': cls})

    def __post_init__(self):
        description = [v for v in [self.__doc__, self.description] if v]
        linebreaks = self.vars.pop(_BR, False)
        var_items_list = [f'{k} = {v}' for k, v in self.vars.items()]
        if linebreaks:
            var_items_str = '[[\n' + '\n'.join(var_items_list) + '\n]]'
        else:
            var_items_str = '[[ ' + ', '.join(var_items_list) + ' ]]'
        self.args = tuple(description + [var_items_str])

    @classmethod
    def br(cls, description: str, _vars: dict[str, Any]):
        """separate each var with linebreaks"""
        _vars[_BR] = True
        return cls(description, _vars)


class NotionDfValueError(NotionDfException, ValueError):
    pass


class NotionDfNotImplementedError(NotionDfException, NotImplementedError):
    pass


@dataclass
class NotionDfStateError(NotionDfException):
    """invalid state is detected."""


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


def remove_falsy_values(d: dict) -> dict:
    return {k: v for k, v in d.items() if v}