from abc import ABC
from itertools import chain
from typing import Hashable, Any, Optional, Iterable, Iterator


class NotionDfException(Exception, ABC):
    """the base exception class."""

    def _set_args(self, params: dict[Hashable, Any] = None, **kwargs: Any) -> tuple[str, ...]:
        items = _concat_items(params, kwargs)
        self.args = (self.__doc__,) + tuple(f'{k} - {v}' for k, v in items)
        return self.args


class NotionDfValueError(NotionDfException, ValueError):
    pass


def repr_object(obj: Any, params: dict[Hashable, Any] = None, **kwargs: Any) -> str:
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
