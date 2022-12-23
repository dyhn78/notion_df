from __future__ import annotations

import functools
import inspect
import types
import typing
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields, InitVar
from datetime import datetime
from enum import Enum
from inspect import isabstract
from typing import Any, final, ClassVar, TypeVar

from typing_extensions import Self

from notion_df.util.misc import NotionDfValueError

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
    if isinstance(serializable, Enum):
        return serializable.value
    if isinstance(serializable, datetime):
        return serializable.isoformat()  # TODO: check Notion time format
    if isinstance(serializable, dict):
        return {k: serialize(v) for k, v in serializable.items()}
    if isinstance(serializable, list) or isinstance(serializable, set):
        return [serialize(e) for e in serializable]
    return serializable


def deserialize(serialized: Any, typ: type):
    """unified serializer for both Serializable and builtin classes."""
    if issubclass(typ, Serializable):
        return typ.deserialize(serialized)
    if isinstance(typ, InitVar):
        return deserialize(serialized, typ.type)
    if issubclass(typ, Enum):
        return typ(serialized)
    if issubclass(typ, datetime):
        return typ.fromisoformat(serialized)
    if isinstance(typ, types.GenericAlias):
        origin: type = typing.get_origin(typ)
        args = typing.get_args(typ)
        if issubclass(origin, dict):
            try:
                value_type = args[1]
            except IndexError:
                value_type = Any
            return {k: deserialize(v, value_type) for k, v in serialized.items()}
        if issubclass(origin, list):
            try:
                element_type = args[0]
            except IndexError:
                element_type = Any
            return [deserialize(e, element_type) for e in serialized]
        if issubclass(origin, set):
            try:
                element_type = args[0]
            except IndexError:
                element_type = Any
            return {deserialize(e, element_type) for e in serialized}
        raise NotImplementedError
    if isinstance(typ, types.UnionType):
        raise NotImplementedError  # TODO: resolve (StrEnum | str) to str
    return serialized


@dataclass
class Resource(Serializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    automatically transforms subclasses into dataclass.
    interchangeable to JSON object."""
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
        dataclass(cls)
        cls._attr_type_dict = {field.name: field.type for field in fields(cls)}

        @dataclass
        class MockSerializable(cls, metaclass=ABCMeta):
            # def __init__(self, **kwargs):
            #     ...

            @classmethod
            def _skip_init_subclass(cls) -> bool:
                return True

            def __getattr__(self, key: str):
                print(self)
                if key in fields(cls):
                    return MockAttribute(key)
                try:
                    return getattr(super(), key)
                except AttributeError:
                    raise NotionDfValueError("cannot parse resource definition", cls, key)

        @dataclass
        class MockAttribute:
            name: str

        init_param_keys = list(inspect.signature(MockSerializable.__init__).parameters.keys())[1:]
        mock_init_param = {k: MockAttribute(k) for k in init_param_keys}
        _mock = MockSerializable(**mock_init_param)  # type: ignore
        for field in fields(MockSerializable):
            setattr(_mock, field.name, MockAttribute(field.name))
        cls._mock_serialized = _mock.serialize()
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
            kwargs[attr_name] = deserialize(value, typ)
        return cls(**kwargs)


@dataclass
class TypedResource(Resource, metaclass=ABCMeta):
    """Resource object with the unified deserializer entrypoint."""
    _registry: ClassVar[dict[KeyChain, type[TypedResource]]] = {}

    def __init_subclass__(cls, **kwargs):
        if cls._skip_init_subclass():
            return
        super().__init_subclass__(**kwargs)
        TypedResource._registry[cls._get_type_keychain(cls._mock_serialized)] = cls

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return isabstract(cls) or cls.deserialize.__code__ != TypedResource.deserialize.__code__

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls is TypedResource:
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
            current_keychain += key,
            if (value := serialized.get(key)) and isinstance(value, dict) and 'type' in value:
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
