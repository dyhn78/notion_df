from abc import ABC
from itertools import chain
from typing import Any


class NotionZapException(Exception, ABC):
    """the base exception class."""
    # TODO: think cooler project name
    pass


def repr_object(obj, params: dict[str, Any] = None, **kwargs: Any) -> str:
    items = chain(params.items() if params is not None else (), kwargs.items())
    return f"{type(obj).__name__}({', '.join(f'{k}={v}' for k, v in items if v is not None)})"


def get_num_iterator():
    num = 0
    while True:
        yield num
        num += 1
