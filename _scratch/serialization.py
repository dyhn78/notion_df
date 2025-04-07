from abc import abstractmethod, ABCMeta
from inspect import isabstract
from typing import Any, Callable, TypeVar, Self, final

from loguru import logger


class Serializable(metaclass=ABCMeta):
    """Representation of the resources defined in Notion REST API.
    Can be dumped into JSON object."""

    @abstractmethod
    def serialize(self) -> Any:
        """:return: python object, instead of JSON string."""


class Deserializable(metaclass=ABCMeta):
    """Representation of the resources defined in Notion REST API.
    Can be loaded from JSON object."""

    @classmethod
    @final
    def deserialize(cls, data: Any) -> Self:
        """:param data: python object, instead of JSON string."""
        if isabstract(cls):
            try:
                get_dispatch_cls = registry__get_dispatch_cls[cls]
            except KeyError:
                raise NotImplementedError(
                    f"Dispatcher not added for the base class. Cannot find a concrete class."
                    f" cls={cls.__name__}"
                )
            dispatch_cls = get_dispatch_cls(data)
            return dispatch_cls.deserialize(data)
        else:
            return cls._deserialize(data)

    @classmethod
    @abstractmethod
    def _deserialize(cls, data: Any) -> Self:
        raise NotImplementedError


registry__get_dispatch_cls: dict[type[Deserializable], Callable[[Any], type[Deserializable]]] = {}


class DualSerializable(Serializable, Deserializable, metaclass=ABCMeta):
    """Dataclass representation of the resources defined in Notion REST API.
    Interchangeable with JSON object."""


TypeDT = TypeVar("TypeDT", bound=type[Deserializable])


class Dispatcher[TypeDT](metaclass=ABCMeta):
    def __init__(self, client_cls: TypeDT) -> None:
        self.client_cls = client_cls
        registry__get_dispatch_cls[client_cls] = self.get_dispatch_cls

    def __repr__(self) -> str:
        return f"{type(self).__name__}({self.client_cls.__name__})"

    @abstractmethod
    def get_dispatch_cls(self, data: dict) -> TypeDT: ...


class TypeBasedDispatcher(Dispatcher[TypeDT]):
    """Dispatch by the value of data["type"], or, typename."""
    _registry: dict[str, type[Deserializable]] = {}

    def register(self, typename: str) -> Callable[[TypeDT], TypeDT]:
        def wrapper(dest_cls: TypeDT) -> TypeDT:
            self._registry[typename] = dest_cls
            return dest_cls

        return wrapper

    def get_dispatch_cls(self, data: dict) -> TypeDT:
        typename = data.get("type")
        try:
            ret = self._registry[typename]
            logger.debug(f"{self}.get_dispatch_cls() => {ret}")
            return ret
        except KeyError:
            raise KeyError(f"{self}.get_dispatch_cls({typename=}, registry={set(self._registry.keys())})")
