from abc import abstractmethod, ABCMeta
from typing import Any, Callable, TypeVar, Protocol, runtime_checkable, Self

TypeT = TypeVar("TypeT", bound=type)
T = TypeVar("T")


class Serializable(metaclass=ABCMeta):
    """representation of the resources defined in Notion REST API.
    can be dumped into JSON object."""

    @abstractmethod
    def serialize(self) -> Any:
        """:return: python object, instead of JSON string."""


@runtime_checkable
class Deserializable(Protocol):
    """representation of the resources defined in Notion REST API.
    can be loaded from JSON object."""

    @classmethod
    def deserialize(cls, data: Any) -> Any:
        """:param data: python object, instead of JSON string."""


class DualSerializable(Serializable, Deserializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable with JSON object."""
    pass


class Concrete(Deserializable, metaclass=ABCMeta):
    @classmethod
    def deserialize(cls, data: Any) -> Self:
        raise NotImplementedError


class Dispatcher[T](Deserializable, metaclass=ABCMeta):
    """Dispatch by the value of data["type"], or, typename."""

    @abstractmethod
    def get_dest_cls(self, data: dict) -> type[Deserializable]: ...

    def deserialize(self, data: Any) -> T:
        return self.get_dest_cls(data).deserialize(data)


class TypebasedDispatcher(Dispatcher[T], metaclass=ABCMeta):
    """Dispatch by the value of data["type"], or, typename."""
    _registry: dict[str, type[Deserializable]] = {}

    def register(self, typename: str) -> Callable[[TypeT], TypeT]:
        def wrapper(dest_cls: TypeT) -> TypeT:
            self._registry[typename] = dest_cls
            return dest_cls

        return wrapper

    def get_dest_cls(self, data: dict) -> type[Deserializable]:
        typename = data["type"]
        return self._registry[typename]
