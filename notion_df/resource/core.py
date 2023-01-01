from __future__ import annotations

import inspect
import types
import typing
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields, InitVar
from datetime import datetime
from enum import Enum
from typing import Any, final, ClassVar

import dateutil.parser
from typing_extensions import Self

from notion_df.util.collection import KeyChain
from notion_df.util.misc import NotionDfValueError
from notion_df.variables import Variables


def serialize_any(obj: Any):
    """unified serializer for both Serializable and builtin classes."""
    if isinstance(obj, dict):
        return {k: serialize_any(v) for k, v in obj.items()}
    if isinstance(obj, list) or isinstance(obj, set):
        return [serialize_any(e) for e in obj]
    if isinstance(obj, Serializable):
        return obj.serialize()
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return DateTimeSerializer.serialize(obj)
    return obj


def deserialize_any(serialized: Any, typ: type):
    """unified serializer for both Serializable and builtin classes."""
    err_description = 'cannot parse serialized value'
    err_vars = {'typ': typ, 'serialized': serialized}
    if isinstance(typ, types.GenericAlias):
        origin: type = typing.get_origin(typ)
        args = typing.get_args(typ)
        try:
            if issubclass(origin, dict):
                value_type = args[1]
                return {k: deserialize_any(v, value_type) for k, v in serialized.items()}
            element_type = args[0]
            if issubclass(origin, list):
                return [deserialize_any(e, element_type) for e in serialized]
            if issubclass(origin, set):
                return {deserialize_any(e, element_type) for e in serialized}
            err_description = 'cannot parse GenericAlias with invalid origin'
        except IndexError:
            err_description = 'cannot parse GenericAlias with invalid args'
        err_vars.update({'typ.origin': origin, 'typ.args': args})
    if isinstance(typ, types.UnionType):
        # TODO: resolve (StrEnum | str) to str - or, is that really needed?
        err_description = 'UnionType is (currently) not supported'
    if inspect.isclass(typ):
        if issubclass(typ, Deserializable):
            return typ.deserialize(serialized)
        if typ in {bool, str, int, float}:
            if type(serialized) == typ:
                return serialized
            err_description = 'serialized value does not match with typ'
        if issubclass(typ, Enum):
            return typ(serialized)
        if issubclass(typ, datetime):
            return DateTimeSerializer.deserialize(serialized)
        if isinstance(typ, InitVar):  # TODO: is this really needed?
            return deserialize_any(serialized, typ.type)
    raise NotionDfValueError(err_description, err_vars)


class DateTimeSerializer:
    @staticmethod
    def get_timezone():
        return Variables.timezone

    @classmethod
    def serialize(cls, dt: datetime):
        return dt.astimezone(cls.get_timezone()).isoformat()  # TODO: check Notion time format

    @classmethod
    def deserialize(cls, dt_string: str):
        datetime_obj = dateutil.parser.parse(dt_string)
        return datetime_obj.astimezone(cls.get_timezone())


@dataclass
class Serializable(metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    transformable into JSON object."""

    def __init__(self, **kwargs):
        pass

    @final
    def serialize(self) -> dict[str, Any]:
        field_value_dict = {f.name: getattr(self, f.name) for f in fields(self)}
        each_field_serialized_obj = type(self)(**{n: serialize_any(v) for n, v in field_value_dict.items()})
        return each_field_serialized_obj.plain_serialize()

    @abstractmethod
    def plain_serialize(self) -> dict[str, Any]:
        """serialize only the first depth structure, leaving each field value not serialized."""
        pass


@dataclass
class Deserializable(Serializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable to JSON object.
    automatically transforms subclasses into dataclass."""
    _field_type_dict: ClassVar[dict[str, type]]
    _field_keychain_dict: ClassVar[dict[KeyChain, str]]
    _mock_serialized: ClassVar[dict[str, Any]]
    _mock = False

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __init_subclass__(cls, **kwargs) -> bool:
        super().__init_subclass__(**kwargs)

        if inspect.isabstract(cls):
            return False

        dataclass(cls)
        cls._field_type_dict = {field.name: field.type for field in fields(cls)}

        if (cls.plain_deserialize.__code__ != Deserializable.plain_deserialize.__code__) or cls._mock:
            # if plain_deserialize() is overridden, in other words, manually configured,
            #  it need not be generated from plain_serialize()
            return False

        @dataclass
        class MockResource(cls, metaclass=ABCMeta):
            _mock = True

            def __getattr__(self, key: str):
                if key in cls._field_type_dict:
                    return MockAttribute(key)
                try:
                    return getattr(super(), key)
                except AttributeError:
                    raise NotionDfValueError("cannot parse resource definition", {'cls': cls, 'key': key})

        @dataclass(frozen=True)
        class MockAttribute:
            name: str

        init_param_keys = list(inspect.signature(MockResource.__init__).parameters.keys())[1:]
        mock_init_param = {k: MockAttribute(k) for k in init_param_keys}
        _mock = MockResource(**mock_init_param)  # type: ignore
        for field in fields(MockResource):
            setattr(_mock, field.name, MockAttribute(field.name))
        cls._mock_serialized = _mock.plain_serialize()
        cls._field_keychain_dict = {}
        items: list[tuple[KeyChain, Any]] = [(KeyChain((k,)), v) for k, v in cls._mock_serialized.items()]
        while items:
            keychain, value = items.pop()
            if isinstance(value, MockAttribute):
                if cls._field_keychain_dict.get(keychain) == value:
                    raise NotionDfValueError(
                        f"serialize() definition cannot have element depending on multiple attributes",
                        {'cls': cls, 'keychain': keychain, '__code__': cls.plain_serialize.__code__},
                        linebreak=True)
                attr_name = value.name
                cls._field_keychain_dict[keychain] = attr_name
            elif isinstance(value, dict):
                items.extend((keychain + (k,), v) for k, v in value.items())
        return True

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        each_field_serialized_dict = cls.plain_deserialize(serialized)
        field_value_dict = {}
        for n, v in each_field_serialized_dict.items():
            field_value_dict[n] = deserialize_any(v, cls._field_type_dict[n])
        return cls(**field_value_dict)

    @classmethod
    def plain_deserialize(cls, serialized: dict[str, Any]) -> dict[str, Any]:
        """return **{field_name: serialized_field_value}."""
        each_field_serialized_dict = {}
        for keychain, n in cls._field_keychain_dict.items():
            each_field_serialized_dict[n] = keychain.get(serialized)
        return each_field_serialized_dict


@dataclass
class TypedResource(Deserializable, metaclass=ABCMeta):
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
