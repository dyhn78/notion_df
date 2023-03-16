from __future__ import annotations

import inspect
import types
import typing
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields, InitVar
from datetime import datetime
from enum import Enum
from typing import Any, final, ClassVar, Optional

import dateutil.parser
from typing_extensions import Self

from notion_df.util.collection import KeyChain, FinalDict
from notion_df.util.misc import NotionDfValueError
from notion_df.variables import Variables


def serialize(obj: Any):
    """unified serializer for both Serializable and external classes."""
    if obj is None:
        return None
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list) or isinstance(obj, set):
        return [serialize(e) for e in obj]
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


def deserialize(serialized: Any, typ: type):
    """unified deserializer for both Deserializable and external classes."""
    err_vars = {'typ': typ, 'serialized': serialized}
    if isinstance(typ, types.GenericAlias):
        origin: type = typing.get_origin(typ)
        args = typing.get_args(typ)
        err_vars.update({'typ.origin': origin, 'typ.args': args})
        try:
            if issubclass(origin, dict):
                value_type = args[1]
                return {k: deserialize(v, value_type) for k, v in serialized.items()}
            element_type = args[0]
            if issubclass(origin, list):
                return [deserialize(e, element_type) for e in serialized]
            if issubclass(origin, set):
                return {deserialize(e, element_type) for e in serialized}
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
        return deserialize(serialized, typ.type)
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
    transformable into JSON object."""

    def __init__(self, **kwargs):
        pass

    @final
    def __init_subclass__(cls, **kwargs):
        """this method is reserved. use cls._init_subclass() instead"""
        super().__init_subclass__(**kwargs)
        if not cls._skip_init_subclass():
            cls.init_subclass(**kwargs)

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return inspect.isabstract(cls) or cls.__name__.startswith('_')

    @classmethod
    def init_subclass(cls, **kwargs) -> None:
        dataclass(cls)

    @final
    def serialize(self) -> dict[str, Any]:
        field_value_dict = {fd.name: getattr(self, fd.name) for fd in fields(self)}
        data_obj_with_each_field_serialized = type(self)(
            **{fd_name: serialize(fd_value) for fd_name, fd_value in field_value_dict.items()})
        return data_obj_with_each_field_serialized._plain_serialize()

    @abstractmethod
    def _plain_serialize(self) -> dict[str, Any]:
        """serialize only the first depth structure, leaving each field value not serialized."""
        pass


@dataclass(frozen=True)
class MockAttribute:
    name: str


@dataclass
class Deserializable(Serializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable to JSON object.
    decorate with '@set_master' to use as a unified deserializer entrypoint."""
    _field_type_dict: ClassVar[dict[str, type]]
    """used to generate deserialize() from parsing _plain_serialize()."""
    _field_keychain_dict: ClassVar[dict[KeyChain, str]]
    """used to generate _plain_deserialize() from parsing _plain_serialize()."""
    mock_serialized: ClassVar[dict[str, Any]]
    """example serialized value but every field is MockAttribute."""
    _subclass_by_keychain_dict: ClassVar[Optional[FinalDict[KeyChain, type[Deserializable]]]]
    """should not be set directly; set by DeserializableResolverByKeyChain decorator."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def init_subclass(cls, **kwargs) -> None:
        super().init_subclass(**kwargs)
        cls._field_type_dict = {field.name: field.type for field in fields(cls)}
        cls.mock_serialized = cls._get_mock_serialized()
        if inspect.getsource(cls._plain_deserialize) != inspect.getsource(Deserializable._plain_deserialize):
            # if _plain_deserialize() is overridden, in other words, manually configured,
            #  it need not be generated from _plain_serialize()
            return
        cls._field_keychain_dict = cls._get_field_keychain_dict(cls.mock_serialized)

    # TODO: support {..., **attr} or {...} | {...} expressions
    #  1. allow MockAttribute supports '**' expression
    #  2. allow _get_field_keychain_dict to recognize blank keychains

    @classmethod
    @final
    def _get_mock_serialized(cls) -> dict[str, Any]:
        @dataclass
        class MockDeserializable(cls, metaclass=ABCMeta):
            @classmethod
            def _skip_init_subclass(cls):
                return True

        MockDeserializable.__name__ = cls.__name__
        init_param_keys = list(inspect.signature(MockDeserializable.__init__).parameters.keys())[1:]
        mock_init_param = {k: MockAttribute(k) for k in init_param_keys}
        _mock = MockDeserializable(**mock_init_param)  # type: ignore
        for field in fields(MockDeserializable):
            setattr(_mock, field.name, MockAttribute(field.name))
        return _mock._plain_serialize()

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        each_field_serialized_dict = cls._plain_deserialize(serialized)
        field_value_dict = {}
        for field_name, field_serialized in each_field_serialized_dict.items():
            field_value_dict[field_name] = deserialize(field_serialized, cls._field_type_dict[field_name])
        return cls(**field_value_dict)  # nomypy

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any]) -> dict[str, Any]:
        """return **{field_name: serialized_field_value}."""
        each_field_serialized_dict = {}
        for keychain, field_name in cls._field_keychain_dict.items():
            each_field_serialized_dict[field_name] = keychain.get(serialized)
        return each_field_serialized_dict

    @classmethod
    def _get_field_keychain_dict(cls, mock_serialized: dict[str, Any]) -> dict[KeyChain, str]:
        # breadth-first search through mock_serialized
        field_keychain_dict = FinalDict[KeyChain, str]()
        items: list[tuple[KeyChain, Any]] = [(KeyChain((k,)), v) for k, v in mock_serialized.items()]
        while items:
            keychain, value = items.pop()
            if isinstance(value, MockAttribute):
                attr_name = value.name
                field_keychain_dict[keychain] = attr_name
            elif isinstance(value, dict):
                items.extend((keychain + (k,), v) for k, v in value.items())
        return field_keychain_dict


Deserializable_T = typing.TypeVar('Deserializable_T', bound=Deserializable)


class DeserializableResolverByKeyChain:
    def __init__(self, unique_key: str):
        self.unique_key = unique_key

    def __call__(self, master: type[Deserializable_T]) -> type[Deserializable_T]:
        if not inspect.isabstract(master):
            raise NotionDfValueError('master class must be abstract', {'master': master})

        master._subclass_by_keychain_dict = subclass_dict = FinalDict[KeyChain, type[Deserializable]]()

        init_subclass_prev = master.init_subclass.__func__  # type: ignore
        deserialize_prev = master.deserialize.__func__  # type: ignore

        def init_subclass(cls: type[Deserializable_T], **kwargs) -> None:
            init_subclass_prev(cls, **kwargs)
            keychain = self.resolve_keychain(cls.mock_serialized)
            subclass_dict[keychain] = cls

        def _deserialize(cls: type[Deserializable_T], serialized: dict[str, Any]) -> Deserializable_T:
            if master != cls:
                return deserialize_prev(cls, serialized)
            keychain = self.resolve_keychain(serialized)
            if keychain not in subclass_dict:
                raise NotionDfValueError('cannot deserialize: unexpected type keychain',
                                         {'master': master, 'keychain': keychain})
            return subclass_dict[keychain].deserialize(serialized)

        master.init_subclass = classmethod(init_subclass)
        master.deserialize = classmethod(_deserialize)
        return master

    def resolve_keychain(self, serialized: dict[str, Any]) -> KeyChain:
        current_keychain = KeyChain()
        if self.unique_key not in serialized:
            raise NotionDfValueError(
                f"cannot resolve keychain: unique key {self.unique_key} not found in serialized data",
                {
                    'unique_key': self.unique_key,
                    'serialized.keys()': list(serialized.keys()),
                    'serialized': serialized
                },
                linebreak=True
            )
        while True:
            key = serialized[self.unique_key]
            current_keychain += key,
            if (value := serialized.get(key)) and isinstance(value, dict) and self.unique_key in value:
                serialized = value
                continue
            return current_keychain


resolve_by_keychain = DeserializableResolverByKeyChain
