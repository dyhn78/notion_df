from __future__ import annotations

import inspect
import types
import typing
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields, InitVar
from datetime import datetime
from enum import Enum
from typing import Any, final, ClassVar, Optional, cast, TypeVar

import dateutil.parser
from typing_extensions import Self

from notion_df.util.collection import KeyChain, FinalDict
from notion_df.util.misc import NotionDfValueError
from notion_df.variables import Variables


def serialize_any(obj: Any):
    """unified serializer for both Serializable and external classes."""
    if isinstance(obj, dict):
        return {k: serialize_any(v) for k, v in obj.items()}
    if isinstance(obj, list) or isinstance(obj, set):
        return [serialize_any(e) for e in obj]
    if isinstance(obj, Serializable):
        return obj.serialize()
    for typ in {bool, str, int, float}:
        if isinstance(obj, typ):
            return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, datetime):
        return DateTimeSerializer.serialize(obj)
    raise NotionDfValueError('cannot serialize', {'obj': obj})


def deserialize_any(serialized: Any, typ: type):
    """unified deserializer for both Deserializable and external classes."""
    err_vars = {'typ': typ, 'serialized': serialized}
    if isinstance(typ, types.GenericAlias):
        origin: type = typing.get_origin(typ)
        args = typing.get_args(typ)
        err_vars.update({'typ.origin': origin, 'typ.args': args})
        try:
            if issubclass(origin, dict):
                value_type = args[1]
                return {k: deserialize_any(v, value_type) for k, v in serialized.items()}
            element_type = args[0]
            if issubclass(origin, list):
                return [deserialize_any(e, element_type) for e in serialized]
            if issubclass(origin, set):
                return {deserialize_any(e, element_type) for e in serialized}
            raise NotionDfValueError('cannot deserialize: GenericAlias type with invalid origin', err_vars)
        except IndexError:
            raise NotionDfValueError('cannot deserialize: GenericAlias type with invalid args', err_vars)
    # TODO: resolve (StrEnum | str) to str - or, is that really needed?
    # if isinstance(typ, types.UnionType):
    #    err_description = 'UnionType is (currently) not supported'
    if not inspect.isclass(typ):
        raise NotionDfValueError('cannot deserialize: not supported type', err_vars)
    if issubclass(typ, Deserializable):
        return typ.deserialize(serialized)
    if typ in {bool, str, int, float}:
        if type(serialized) != typ:
            raise NotionDfValueError('cannot deserialize: type(serialized) != typ', err_vars)
        return serialized
    if issubclass(typ, Enum):
        return typ(serialized)
    if issubclass(typ, datetime):
        return DateTimeSerializer.deserialize(serialized)
    if isinstance(typ, InitVar):  # TODO: is this really needed?
        return deserialize_any(serialized, typ.type)
    raise NotionDfValueError('cannot deserialize: not supported class', err_vars)


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
    transformable into JSON object.
    automatically transforms subclasses into dataclass."""

    def __init__(self, **kwargs):
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        dataclass(cls)

    @final
    def serialize(self) -> dict[str, Any]:
        field_value_dict = {f.name: getattr(self, f.name) for f in fields(self)}
        each_field_serialized_obj = type(self)(**{n: serialize_any(v) for n, v in field_value_dict.items()})
        return each_field_serialized_obj.plain_serialize()

    @abstractmethod
    def plain_serialize(self) -> dict[str, Any]:
        """serialize only the first depth structure, leaving each field value not serialized."""
        pass


_Deserializable_T = TypeVar('_Deserializable_T', bound='Deserializable')


class _DeserializableRegistry:
    """data structure to handle master-subclasses relation of deserializable classes."""

    def __init__(self):
        self.data: dict[type[Deserializable], FinalDict[KeyChain, type[Deserializable]]] = {}
        """schema: '{master: {keychain: {subclasses} } }'"""

    def set_master(self, master: type[_Deserializable_T]) -> type[_Deserializable_T]:
        """decorator that set an abstract base deserializable class a representative resource,
        allowing it to distinguish its several subclasses' serialized form."""
        if not inspect.isabstract(master):
            raise NotionDfValueError('master class must be abstract', {'cls': master})
        self.data[master] = FinalDict()
        return master

    def is_master(self, master: type[Deserializable]) -> bool:
        return master in self.data

    def get_master(self, subclass: type[Deserializable]) -> Optional[type[Deserializable]]:
        for base in subclass.__mro__:
            base = cast(type[Deserializable], base)
            if issubclass(base, Deserializable) and self.is_master(base):
                return base
        return None

    def set_subclass(self, subclass: type[Deserializable], subclass_mock_serialized: dict[str, Any]):
        if not (master := self.get_master(subclass)):
            return
        subclass_type_keychain = self.get_type_keychain(subclass_mock_serialized)
        self.data[master][subclass_type_keychain] = subclass

    def get_subclass(self, master: type[Deserializable], serialized: dict[str, Any]) -> Optional[type[Deserializable]]:
        if not self.is_master(master):
            return None
        type_keychain = self.get_type_keychain(serialized)
        return self.data[master][type_keychain]

    @staticmethod
    def get_type_keychain(serialized: dict[str, Any]) -> KeyChain:
        current_keychain = KeyChain()
        if 'type' not in serialized:
            raise NotionDfValueError(
                "cannot deserialize via master: 'type' key not found in serialized data",
                {'serialized.keys()': list(serialized.keys()), 'serialized': serialized},
                linebreak=True
            )
        while True:
            key = serialized['type']
            current_keychain += key,
            if (value := serialized.get(key)) and isinstance(value, dict) and 'type' in value:
                serialized = value
                continue
            return current_keychain


_deserializable_registry = _DeserializableRegistry()
set_master = _deserializable_registry.set_master


@dataclass
class Deserializable(Serializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable to JSON object.
    automatically transforms subclasses into dataclass.
    if decorated with '@set_master', it also provides a unified deserializer entrypoint."""
    _mock: ClassVar[bool] = False
    _field_type_dict: ClassVar[dict[str, type]]
    _field_keychain_dict: ClassVar[dict[KeyChain, str]]
    __registry: ClassVar[_DeserializableRegistry] = _deserializable_registry

    @dataclass(frozen=True)
    class _MockAttribute:
        name: str

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    @final
    def _skip_init_subclass(cls) -> bool:
        return cls._mock or inspect.isabstract(cls) or cls.__name__.startswith('_')

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls._skip_init_subclass():
            return

        cls._field_type_dict = {field.name: field.type for field in fields(cls)}
        mock_serialized = cls._get_mock_serialized()
        cls.__registry.set_subclass(cls, mock_serialized)
        if cls.plain_deserialize.__code__ != Deserializable.plain_deserialize.__code__:
            # if plain_deserialize() is overridden, in other words, manually configured,
            #  it need not be generated from plain_serialize()
            return
        cls._field_keychain_dict = cls._get_field_keychain_dict(mock_serialized)

    @classmethod
    def _get_mock_serialized(cls) -> dict[str, Any]:
        @dataclass
        class MockResource(cls, metaclass=ABCMeta):
            _mock = True

        MockResource.__name__ = cls.__name__
        init_param_keys = list(inspect.signature(MockResource.__init__).parameters.keys())[1:]
        mock_init_param = {k: cls._MockAttribute(k) for k in init_param_keys}
        _mock = MockResource(**mock_init_param)  # type: ignore
        for field in fields(MockResource):
            setattr(_mock, field.name, cls._MockAttribute(field.name))
        return _mock.plain_serialize()

    @classmethod
    def _get_field_keychain_dict(cls, mock_serialized: dict[str, Any]) -> dict[KeyChain, str]:
        field_keychain_dict = FinalDict[KeyChain, str]()
        items: list[tuple[KeyChain, Any]] = [(KeyChain((k,)), v) for k, v in mock_serialized.items()]
        while items:
            keychain, value = items.pop()
            if isinstance(value, cls._MockAttribute):
                attr_name = value.name
                field_keychain_dict[keychain] = attr_name
            elif isinstance(value, dict):
                items.extend((keychain + (k,), v) for k, v in value.items())
        return field_keychain_dict

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if subclass := cls.__registry.get_subclass(cls, serialized):
            return subclass.deserialize(serialized)

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
