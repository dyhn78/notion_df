from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass
from datetime import datetime
from inspect import isabstract
from typing import Any, final, ClassVar, TypeVar

from typing_extensions import Self

from notion_df.util.util import NotionDfValueError

_T = TypeVar('_T')
KeyChain = tuple[str, ...]


def get_item(d: dict, key_chain: KeyChain):
    value = d
    for key in key_chain:
        value = value[key]
    return value


@dataclass
class Serializable(metaclass=ABCMeta):
    """base dataclass used for Notion-df. interchangeable to JSON."""

    @abstractmethod
    def serialize(self):
        pass

    @classmethod
    @abstractmethod
    def deserialize(cls, serialized) -> Self:
        pass


class ExternalSerializable(Serializable, metaclass=ABCMeta):
    """provide unified Serialization interface for external classes, such as datetime.
    to 'register' a class, inherit this class and implement serialize() / deserialize() methods."""
    registry: dict[type, type[ExternalSerializable]] = {}

    def __init_subclass__(cls, **kwargs):
        origin = None
        for base in cls.__mro__:
            if not issubclass(base, ExternalSerializable):
                origin = base
                break
        assert origin is not None, f"no base class found for {cls}"
        ExternalSerializable.registry[origin] = cls

    @classmethod
    def serialize_any(cls, external_cls: Any):
        """unified serializer for external classes."""
        external_serializer = cls.registry[type(external_cls)]
        return external_serializer.serialize(external_cls)

    @classmethod
    def deserialize_any(cls, typ: type[_T], serialized) -> _T:
        """unified deserializer for external classes."""
        external_serializer = cls.registry[typ]
        return external_serializer.deserialize(serialized)


serialize = ExternalSerializable.serialize_any
deserialize = ExternalSerializable.deserialize_any


class DateTime(datetime, ExternalSerializable):
    def serialize(self):
        return self.isoformat()

    @classmethod
    def deserialize(cls, serialized):
        return datetime.fromisoformat(serialized)


@dataclass
class ObjectSerializable(Serializable, metaclass=ABCMeta):
    """base dataclass used for Notion-df. interchangeable to JSON object."""
    _attr_name_dict: ClassVar[dict[KeyChain, str]]
    _mock_serialized: ClassVar[dict]

    def __init__(self, **kwargs):
        pass

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return isabstract(cls) or cls.deserialize.__code__ != ObjectSerializable.deserialize.__code__

    def __init_subclass__(cls, **kwargs):
        # TODO: auto-wrap serialize() and deserialize() ::
        #  serialize() : convert s -> serialize(s) for return dictionary values
        #  deserialize() : convert s -> deserialize(typ, s) for return kwargs
        #  to achieve this, serialize() and deserialize() should be available
        #  for both InternalSerializable and ExternalSerializable
        if cls._skip_init_subclass():
            return
        super().__init_subclass__(**kwargs)

        @dataclass
        class MockSerializable(cls, metaclass=ABCMeta):
            def __getattr__(self, key: str):
                try:
                    return getattr(super(), key)
                except AttributeError:
                    return MockAttribute(key)

            @classmethod
            def _skip_init_subclass(cls) -> bool:
                return True

        cls._mock_serialized = MockSerializable().serialize()

        cls._attr_name_dict = {}
        items: list[tuple[KeyChain, Any]] = [((k,), v) for k, v in cls._mock_serialized.items()]
        while items:
            key_chain, value = items.pop()
            if isinstance(value, MockAttribute):
                if cls._attr_name_dict.get(key_chain) == value:
                    raise NotionDfValueError(
                        f"serialize() definition cannot have element depending on multiple attributes")
                cls._attr_name_dict[key_chain] = value.name
            elif isinstance(value, dict):
                items.extend((key_chain + (k,), v) for k, v in value.items())

    @classmethod
    def deserialize(cls, serialized: dict) -> Self:
        return cls(**{attr_name: get_item(serialized, key_chain)
                      for key_chain, attr_name in cls._attr_name_dict.items()})


@dataclass
class MockAttribute:
    name: str


@dataclass
class Resource(ObjectSerializable):
    """representation of the resources defined in Notion REST API.
    interchangeable to JSON object. has a unified deserializer."""
    _registry: ClassVar[dict[KeyChain, type[Resource]]] = {}

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return isabstract(cls) or cls.deserialize.__code__ != Resource.deserialize.__code__

    def __init_subclass__(cls, **kwargs):
        if cls._skip_init_subclass():
            return
        super().__init_subclass__(**kwargs)
        Resource._registry[cls._get_type_key_chain(cls._mock_serialized)] = cls

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        pass

    @classmethod
    def deserialize(cls, serialized: dict) -> Self:
        if cls is Resource:
            subclass = cls._registry[cls._get_type_key_chain(serialized)]
            return subclass.deserialize(serialized)
        return super().deserialize(serialized)

    @staticmethod
    @final
    def _get_type_key_chain(serialized: dict) -> KeyChain:
        current_key_chain = ()
        if 'type' not in serialized:
            raise NotionDfValueError(f"'type' not in d :: {serialized.keys()=}")
        while True:
            key = serialized['type']
            value = serialized[key]
            current_key_chain += key,
            if isinstance(value, dict) and 'type' in value:
                serialized = value
                continue
            return current_key_chain


@dataclass
class PlainSerializable(Serializable):
    data: Any

    def serialize(self):
        return self.data

    @classmethod
    def deserialize(cls, serialized) -> Self:
        return cls(serialized)
