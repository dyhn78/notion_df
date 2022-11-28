from abc import ABC, abstractmethod
from typing import Any, Generic, TypeVar, Callable, ParamSpec

_T = TypeVar('_T')
_P = ParamSpec('_P')


class Dictable(ABC):
    def __init_subclass__(cls, **kwargs):
        ...  # TODO: register class to deserialize() - https://www.notion.so/dyhn/df-Serializable-Trie-0607a9f6456a46ed875f7df404ab82b0

    @abstractmethod
    def to_dict(self) -> dict[str, Any]: ...


# class Dictable2(Dictable):
#     @classmethod
#     @abstractmethod
#     def from_dict(cls, value: dict) -> Self: ...

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
