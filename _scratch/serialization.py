from abc import abstractmethod, ABCMeta
from typing import Any, Callable, TypeVar, Protocol, runtime_checkable, Self

from loguru import logger

TypeT = TypeVar("TypeT", bound=type)
T = TypeVar("T")


class Serializable(metaclass=ABCMeta):
    """Representation of the resources defined in Notion REST API.
    Can be dumped into JSON object."""

    @abstractmethod
    def serialize(self) -> Any:
        """:return: python object, instead of JSON string."""


@runtime_checkable
class Deserializable(Protocol):
    """Representation of the resources defined in Notion REST API.
    Can be loaded from JSON object."""

    @classmethod
    def deserialize(cls, data: Any) -> Any:
        """:param data: python object, instead of JSON string."""


class Concrete(Serializable, Deserializable, metaclass=ABCMeta):
    """Classes which can deserialize into itself."""

    @classmethod
    @abstractmethod
    def deserialize(cls, data: Any) -> Self:
        raise NotImplementedError


class Dispatcher[T](Deserializable, metaclass=ABCMeta):
    @abstractmethod
    def get_dispatch_target(self, data: dict) -> type[Deserializable]: ...

    def deserialize(self, data: Any) -> T:
        return self.get_dispatch_target(data).deserialize(data)


# TODO: clean TypeVars
class TypenameDispatcher(Dispatcher[T]):
    """Dispatch by the value of data["type"], or, typename."""
    _registry: dict[str, type[Deserializable]] = {}

    def __init__(self, name: str):
        """:param name: must be same as the variable name"""
        self.name = name

    def __repr__(self) -> str:
        return self.name

    def register(self, typename: str) -> Callable[[TypeT], TypeT]:
        def wrapper(dest_cls: TypeT) -> TypeT:
            self._registry[typename] = dest_cls
            return dest_cls

        return wrapper

    def get_dispatch_target(self, data: dict) -> type[Deserializable]:
        typename = data.get("type")
        try:
            ret = self._registry[typename]
            logger.debug(f"{self}.get_dispatch_target() => {ret}")
            return ret
        except KeyError:
            raise KeyError(f"{self}.get_dispatch_target({typename=}, registry={set(self._registry.keys())})")
