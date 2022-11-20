from abc import ABC
from itertools import chain
from typing import Any, Optional, Iterable, cast, Hashable


class NotionZapException(Exception, ABC):
    """the base exception class."""

    # TODO: think cooler project name
    def _set_args(self, params: dict[Hashable, Any] = None, **kwargs: Any) -> tuple[str, ...]:
        items = _get_items(params, kwargs)
        self.args = (self.__doc__,) + tuple(f'{k} - {v}' for k, v in items)
        return self.args


def repr_object(obj: Any, params: dict[Hashable, Any] = None, **kwargs: Any) -> str:
    """params and kwargs has same effect"""
    items = _get_items(params, kwargs)
    return f"{type(obj).__name__}({', '.join(f'{k}={v}' for k, v in items if v is not None)})"


def _get_items(params: Optional[dict[Hashable, Any]], kwargs: dict[str, Any]) \
        -> Iterable[tuple[Hashable, str]]:
    return cast(Iterable[tuple[Hashable, str]],
                chain(params.items() if params is not None else (), kwargs.items()))


def get_num_iterator() -> Iterable[int]:
    num = 0
    while True:
        yield num
        num += 1
