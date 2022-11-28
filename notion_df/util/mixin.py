from __future__ import annotations

from abc import abstractmethod
from typing import Generic, TypeVar, Callable, ParamSpec

_T = TypeVar('_T')
_P = ParamSpec('_P')


class Resolvable(Generic[_T]):
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
