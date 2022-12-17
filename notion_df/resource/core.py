from __future__ import annotations

import functools
from abc import abstractmethod, ABCMeta
from copy import copy, deepcopy
from dataclasses import dataclass, fields
from datetime import datetime
from inspect import isabstract
from typing import Any, final, ClassVar, TypeVar, Optional

from typing_extensions import Self

from notion_df.util.collection import StrEnum
from notion_df.util.util import NotionDfValueError

_T = TypeVar('_T')
KeyChain = tuple[str, ...]


def get_item(d: dict, keychain: KeyChain) -> Any:
    for key in keychain:
        d = d[key]
    return d


def set_item(d: dict, keychain: KeyChain, value) -> None:
    if not keychain:
        return
    for key in keychain[:-1]:
        d = d[key]
    d[keychain[-1]] = value


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


def serialize(serializable: Any):
    """unified serializer for both Serializable and builtin classes."""
    if isinstance(serializable, Serializable):
        return serializable.serialize()
    if isinstance(serializable, datetime):
        return serializable.isoformat()  # TODO: check Notion time format
    if isinstance(serializable, StrEnum):
        return serializable.value
    return serializable


def deserialize(serialized: Any, typ: Optional[type[_T]] = None) -> _T:
    """unified serializer for both Serializable and builtin classes."""
    if issubclass(typ, Serializable):
        return typ.deserialize(serialized)
    if typ == datetime:
        return datetime.fromisoformat(serialized)
    if issubclass(typ, StrEnum):  # type: ignore
        return typ(serialized)
    return serialized


@dataclass
class Resource(Serializable, metaclass=ABCMeta):
    """representation of the resources defined in Notion REST API. interchangeable to JSON object."""
    _attr_type_dict: ClassVar[dict[str, type]]
    _attr_location_dict: ClassVar[dict[KeyChain, str]]
    _mock_serialized: ClassVar[dict[str, Any]]

    def __init__(self, **kwargs):
        pass

    def __post_init__(self):
        ...

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return isabstract(cls) or cls.deserialize.__code__ != Resource.deserialize.__code__

    def __init_subclass__(cls, **kwargs):
        """NOTE: when overriding, you should call super method on end of the definition
        (to properly auto-decorate methods)"""
        if cls._skip_init_subclass():
            return
        super().__init_subclass__(**kwargs)

        @dataclass
        class MockSerializable(cls, metaclass=ABCMeta):
            @classmethod
            def _skip_init_subclass(cls) -> bool:
                return True

            def __getattribute__(self, key: str):
                if key in cls.__annotations__:
                    return MockAttribute(key)
                try:
                    return getattr(super(), key)
                except AttributeError:
                    raise NotionDfValueError("cannot parse resource definition", cls, key)

        @dataclass
        class MockAttribute:
            name: str

        cls._mock_serialized = MockSerializable().serialize()
        cls._attr_location_dict = {}
        items: list[tuple[KeyChain, Any]] = [((k,), v) for k, v in cls._mock_serialized.items()]
        while items:
            keychain, value = items.pop()
            if isinstance(value, MockAttribute):
                if cls._attr_location_dict.get(keychain) == value:
                    raise NotionDfValueError(
                        f"serialize() definition cannot have element depending on multiple attributes")
                attr_name = value.name
                cls._attr_location_dict[keychain] = attr_name
            elif isinstance(value, dict):
                items.extend((keychain + (k,), v) for k, v in value.items())

        plain_serialize = cls.serialize

        @functools.wraps(cls.serialize)
        def wrap_serialize(self: cls):
            serialized = plain_serialize(self)
            for _keychain, _attr_name in cls._attr_location_dict.items():
                _value = get_item(serialized, _keychain)
                set_item(serialized, _keychain, serialize(_value))
            return serialized

        cls.serialize = wrap_serialize

        dataclass(cls)
        cls._attr_type_dict = {field.name: field.type for field in fields(cls)}

    @abstractmethod
    def serialize(self) -> dict[str, Any]:
        """NOTE: this method automatically serialize nested attributes."""
        pass

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        """NOTE: this method automatically deserialize nested attributes."""
        kwargs = {}
        for keychain, attr_name in cls._attr_location_dict.items():
            typ = cls._attr_type_dict[attr_name]
            value = get_item(serialized, keychain)
            kwargs[attr_name] = deserialize(value, typ)  # type: ignore
        return cls(**kwargs)


@dataclass
class UniqueResource(Resource, metaclass=ABCMeta):
    """Resource object with a unified deserializer entrypoint."""
    _registry: ClassVar[dict[KeyChain, type[UniqueResource]]] = {}

    def __init_subclass__(cls, **kwargs):
        if cls._skip_init_subclass():
            return
        super().__init_subclass__(**kwargs)
        UniqueResource._registry[cls._get_type_keychain(cls._mock_serialized)] = cls

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return isabstract(cls) or cls.deserialize.__code__ != UniqueResource.deserialize.__code__

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls is UniqueResource:
            subclass = cls._registry[cls._get_type_keychain(serialized)]
            return subclass.deserialize(serialized)
        return super().deserialize(serialized)

    @staticmethod
    @final
    def _get_type_keychain(serialized: dict[str, Any]) -> KeyChain:
        current_keychain = ()
        if 'type' not in serialized:
            raise NotionDfValueError(f"'type' not in d :: {serialized.keys()=}")
        while True:
            key = serialized['type']
            value = serialized[key]
            current_keychain += key,
            if isinstance(value, dict) and 'type' in value:
                serialized = value
                continue
            return current_keychain


@dataclass
class PlainSerializable(Serializable):
    data: Any

    def serialize(self):
        return self.data

    @classmethod
    def deserialize(cls, serialized) -> Self:
        return cls(serialized)
