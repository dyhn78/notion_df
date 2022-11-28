from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Callable, ParamSpec, Final, final

from typing_extensions import Self

_T = TypeVar('_T')
_P = ParamSpec('_P')


class Trie(Generic[_T]):
    def __init__(self):
        ...

    def __getitem__(self, key: tuple[str, ...]) -> _T:
        ...

    def __setitem__(self, key: tuple[str, ...], value: _T):
        ...


class Dictable(ABC):
    registry = Final[Trie[Self]]()

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        self = cls()  # TODO: initiate cls with default values (ex) None, object()
        full_path = Dictable.find_type_key(self.to_dict())
        Dictable.registry[full_path] = cls

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        pass

    @classmethod
    @abstractmethod
    def from_dict(cls, d: dict) -> Self:
        subclass = cls.registry[cls.find_type_key(d)]
        return subclass.from_dict(d)

    @classmethod
    @final
    def find_type_key(cls, d: dict) -> tuple[str, ...]:
        """
        find the key "type". if d[d[type]] is a string, return. if it is a dict, repeat. keep the whole path.
        if there is no key 'type', or d[type] is not string or dict, raise ValueError.
        return (full_path, value)
        """


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
