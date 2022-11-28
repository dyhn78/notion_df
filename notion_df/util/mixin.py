from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Callable, ParamSpec, Final, final

from typing_extensions import Self

_T = TypeVar('_T')
_P = ParamSpec('_P')


class DataObject(ABC):
    """base dataclass used to communicate with Notion API. interoperable to JSON object."""
    registry: Final[dict[tuple[str, ...], Self]] = {}

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        self = cls()  # TODO: initiate cls with default values (ex) None, object()
        full_key = DataObject.find_api_type(self.to_dict())
        DataObject.registry[full_key] = cls

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> Self:
        subclass = cls.registry[cls.find_api_type(d)]
        return subclass.from_dict(d)

    @classmethod
    @final
    def find_api_type(cls, d: dict) -> tuple[str, ...]:
        """
        find the key "type". if d[d[type]] is a string, return the full path.
        if it is a dict, repeat while keeping the whole path.
        if there is no key 'type', or d[type] is not string or dict, raise ValueError.
        """
        full_key = []
        while True:
            if 'type' not in d:
                raise ValueError(f"'type' not in d :: {d.keys()=}")
            key = d['type']
            value = d[key]
            full_key.append(key)
            if isinstance(value, str):
                return tuple(full_key)
            if isinstance(value, dict):
                d = value
                continue
            raise ValueError(f"d[{full_key}] is not a string nor an object :: d[{full_key}]={value}")


class Promise(Generic[_T]):
    @abstractmethod
    def resolve(self) -> _T:
        pass


def input_based_cache(func: Callable[_P, _T]) -> Callable[_P, _T]:
    cache: dict[tuple, _T] = {}

    def wrapper(*args, **kwargs):
        cache_key = args + tuple((k, v) for k, v in kwargs.items())
        if cache_value := cache.get(cache_key):
            return cache_value
        new_value = func(*args, **kwargs)
        cache[cache_key] = new_value
        return new_value

    return wrapper
