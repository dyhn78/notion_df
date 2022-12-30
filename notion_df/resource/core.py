from __future__ import annotations

import inspect
import types
import typing
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields, InitVar
from datetime import datetime
from enum import Enum
from typing import Any, final, ClassVar

from typing_extensions import Self

from notion_df.util.collection import KeyChain
from notion_df.util.misc import NotionDfValueError


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
    err_description = 'cannot parse serialized value'
    err_vars = {'typ': typ, 'serialized': serialized}
    if isinstance(typ, types.GenericAlias):
        origin: type = typing.get_origin(typ)
        args = typing.get_args(typ)
        try:
            if issubclass(origin, dict):
                value_type = args[1]
                return {k: deserialize(v, value_type) for k, v in serialized.items()}
            element_type = args[0]
            if issubclass(origin, list):
                return [deserialize(e, element_type) for e in serialized]
            if issubclass(origin, set):
                return {deserialize(e, element_type) for e in serialized}
            err_description = 'cannot parse GenericAlias with invalid origin'
        except IndexError:
            err_description = 'cannot parse GenericAlias with invalid args'
        err_vars.update({'typ.origin': origin, 'typ.args': args})
    if isinstance(typ, types.UnionType):
        # TODO: resolve (StrEnum | str) to str - or, is that really needed?
        err_description = 'UnionType is (currently) not supported'
    if inspect.isclass(typ):
        if issubclass(typ, Serializable):
            return typ.deserialize(serialized)
        if typ in {bool, str, int, float}:
            if type(serialized) == typ:
                return serialized
            err_description = 'serialized value does not match with typ'
        if issubclass(typ, Enum):
            return typ(serialized)
        if issubclass(typ, datetime):
            return typ.fromisoformat(serialized)
        if isinstance(typ, InitVar):  # TODO: is this really needed?
            return deserialize(serialized, typ.type)
    raise NotionDfValueError(err_description, err_vars)


@dataclass
class PlainSerializable(Serializable):
    data: Any

    def serialize(self):
        return self.data

    @classmethod
    def deserialize(cls, serialized) -> Self:
        return cls(serialized)


@dataclass
class Resource(Serializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    automatically transforms subclasses into dataclass.
    interchangeable to JSON object."""
    _field_type_dict: ClassVar[dict[str, type]]
    _field_location_dict: ClassVar[dict[KeyChain, str]]
    _mock_serialized: ClassVar[dict[str, Any]]

    def __init__(self, **kwargs):
        pass

    def __post_init__(self):
        ...

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return inspect.isabstract(
            cls) or cls.deserialize_plain.__code__ != Resource.deserialize_plain.__code__

    def __init_subclass__(cls, **kwargs) -> bool:
        super().__init_subclass__(**kwargs)
        if cls._skip_init_subclass():
            return False

        dataclass(cls)
        cls._field_type_dict = {field.name: field.type for field in fields(cls)}

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
                    raise NotionDfValueError("cannot parse resource definition", {'cls': cls, 'key': key})

        @dataclass
        class MockAttribute:
            name: str

        init_param_keys = list(inspect.signature(MockSerializable.__init__).parameters.keys())[1:]
        mock_init_param = {k: MockAttribute(k) for k in init_param_keys}
        _mock = MockSerializable(**mock_init_param)  # type: ignore
        for field in fields(MockSerializable):
            setattr(_mock, field.name, MockAttribute(field.name))
        cls._mock_serialized = _mock.serialize_plain()
        cls._field_location_dict = {}
        items: list[tuple[KeyChain, Any]] = [(KeyChain((k,)), v) for k, v in cls._mock_serialized.items()]
        while items:
            keychain, value = items.pop()
            if isinstance(value, MockAttribute):
                if cls._field_location_dict.get(keychain) == value:
                    raise NotionDfValueError(
                        f"serialize() definition cannot have element depending on multiple attributes",
                        {'cls': cls, 'keychain': keychain, '__code__': cls.serialize_plain.__code__},
                        linebreak=True)
                attr_name = value.name
                cls._field_location_dict[keychain] = attr_name
            elif isinstance(value, dict):
                items.extend((keychain + (k,), v) for k, v in value.items())
        return True

    @final
    def serialize(self):
        field_value_dict = {f.name: getattr(self, f.name) for f in fields(self)}
        each_field_serialized_obj = type(self)(**{n: serialize(v) for n, v in field_value_dict.items()})
        return each_field_serialized_obj.serialize_plain()

    @abstractmethod
    def serialize_plain(self) -> dict[str, Any]:
        """serialize only the first depth structure, leaving each field value not serialized."""
        pass

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        each_field_serialized_dict = cls.deserialize_plain(serialized)
        field_value_dict = {}
        for n, v in each_field_serialized_dict.items():
            field_value_dict[n] = deserialize(v, cls._field_type_dict[n])
        return cls(**field_value_dict)

    @classmethod
    def deserialize_plain(cls, serialized: dict[str, Any]) -> dict[str, Any]:
        """return **{field_name: serialized_field_value}."""
        each_field_serialized_dict = {}
        for keychain, n in cls._field_location_dict.items():
            each_field_serialized_dict[n] = keychain.get(serialized)
        return each_field_serialized_dict


@dataclass
class TypedResource(Resource, metaclass=ABCMeta):
    """Resource object with the unified deserializer entrypoint."""
    _registry: ClassVar[dict[KeyChain, type[TypedResource]]] = {}

    def __init_subclass__(cls, **kwargs):
        if super().__init_subclass__(**kwargs):
            TypedResource._registry[cls._get_type_keychain(cls._mock_serialized)] = cls

    # noinspection PyFinal
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
        current_keychain = KeyChain()
        if 'type' not in serialized:
            raise NotionDfValueError(f"'type' key not found",
                                     {'serialized.keys()': list(serialized.keys()), 'serialized': serialized},
                                     linebreak=True)
        while True:
            key = serialized['type']
            current_keychain += key,
            if (value := serialized.get(key)) and isinstance(value, dict) and 'type' in value:
                serialized = value
                continue
            return current_keychain
