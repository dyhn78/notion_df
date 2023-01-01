from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Generic, TypeVar, Callable, ParamSpec, ClassVar

from typing_extensions import Self

_T = TypeVar('_T')
_P = ParamSpec('_P')


class Resolvable(Generic[_T]):
    @abstractmethod
    def resolve(self) -> _T:
        pass


def cache_on_input(func: Callable[_P, _T]) -> Callable[_P, _T]:
    cache: dict[tuple, _T] = {}

    def wrapper(*args, **kwargs):
        cache_key = args + tuple((k, v) for k, v in kwargs.items())
        if cache_value := cache.get(cache_key):
            return cache_value
        new_value = func(*args, **kwargs)
        cache[cache_key] = new_value
        return new_value

    return wrapper


class SingletonOnInput(metaclass=ABCMeta):
    """singleton based on __init__ arguments, which must only contain immutable classes."""
    # reference: https://stackoverflow.com/questions/6764338/how-to-create-a-singleton-class-based-on-its-input
    instances: ClassVar[dict[tuple, Self]] = {}

    def __new__(cls, *args, **kwargs):
        cache_key = args + tuple((k, v) for k, v in kwargs.items())
        assert hash(cache_key)
        if cache_key not in cls.instances:
            cls.instances[cache_key] = super().__new__(cls)
        return cls.instances[cache_key]
