from __future__ import annotations

import inspect
import types
import typing
from abc import abstractmethod, ABCMeta
from dataclasses import dataclass, fields, InitVar
from datetime import datetime
from enum import Enum
from functools import cache
from typing import Any, final, ClassVar, Optional

import dateutil.parser
from typing_extensions import Self

from notion_df.util.collection import Keychain, FinalDict
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

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if not inspect.isabstract(cls):
            dataclass(cls)

    @classmethod
    def _skip_init_subclass(cls) -> bool:
        return False

    @abstractmethod
    def _plain_serialize(self) -> dict[str, Any]:
        """serialize only the first depth structure, leaving each field value not serialized."""
        pass

    @final
    def serialize(self) -> dict[str, Any]:
        field_value_dict = {fd.name: getattr(self, fd.name) for fd in fields(self)}
        data_obj_with_each_field_serialized = type(self)(
            **{fd_name: serialize(fd_value) for fd_name, fd_value in field_value_dict.items()})
        return data_obj_with_each_field_serialized._plain_serialize()


@dataclass
class Deserializable(Serializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable to JSON object."""
    _subclass_by_keychain_dict: ClassVar[Optional[FinalDict[Keychain, type[Deserializable]]]]
    """should not be set directly; set by DeserializableResolverByKeyChain decorator."""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars: Any) -> Self:
        """return cls(**{field_name: field_serialized}).

        Note: override this method if plain_serialize() definition is not parsable."""
        each_field_serialized_dict = {}
        for keychain, field_name in cls._get_field_keychain_dict().items():
            field_serialized = serialized
            for key in keychain:
                if isinstance(key, MockAttribute):
                    key = field_vars[key.name]
                field_serialized = field_serialized[key]
            each_field_serialized_dict[field_name] = field_serialized
        return cls(**each_field_serialized_dict)

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        """Note: override this method if you need to implement a unified deserializer entrypoint."""
        plain_self = cls._plain_deserialize(serialized)
        print(plain_self)
        for field in fields(plain_self):
            setattr(plain_self, field.name, deserialize(getattr(plain_self, field.name), field.type))
        return plain_self

    @classmethod
    @final
    @cache
    def get_mock_serialized(cls) -> dict[str, Any]:
        """example serialized value by _plain_serialize(), with every field is replaced as MockAttribute.
        used to generate _plain_deserialize()."""

        # TODO: support {..., **attr} or {...} | {...} expressions
        #  1. allow MockAttribute supports '**' expression
        #  2. allow _get_field_keychain_dict to recognize blank keychains

        __init_subclass__ = getattr(cls, '__init_subclass__').__func__
        setattr(cls, '__init_subclass__', lambda **kwargs: None)

        @dataclass
        class MockDeserializable(cls, metaclass=ABCMeta):
            @classmethod
            def _skip_init_subclass(cls):
                return True

        setattr(cls, '__init_subclass__', classmethod(__init_subclass__))

        MockDeserializable.__name__ = cls.__name__
        init_params = list(inspect.signature(MockDeserializable.__init__).parameters.keys())[1:]
        mock_init_param = {param: MockAttribute(param) for param in init_params}
        _mock = MockDeserializable(**mock_init_param)  # type: ignore
        for field in fields(MockDeserializable):
            setattr(_mock, field.name, MockAttribute(field.name))
        try:
            return _mock._plain_serialize()
        except AttributeError:
            raise NotionDfValueError('_plain_serialize() not parsable', {'cls': cls})

    @classmethod
    @cache
    def _get_field_type_dict(cls) -> dict[str, type]:
        return {field.name: field.type for field in fields(cls)}

    @classmethod
    @cache
    def _get_field_keychain_dict(cls) -> dict[Keychain, str]:
        # breadth-first search through mock_serialized
        field_keychain_dict = FinalDict[Keychain, str]()
        items: list[tuple[Keychain, Any]] = [(Keychain((k,)), v) for k, v in cls.get_mock_serialized().items()]
        while items:
            keychain, value = items.pop()
            if isinstance(value, MockAttribute):
                attr_name = value.name
                field_keychain_dict[keychain] = attr_name
            elif isinstance(value, dict):
                items.extend((Keychain(keychain + (k,)), v) for k, v in value.items())
        return field_keychain_dict


@dataclass(frozen=True)
class MockAttribute:
    name: str


Deserializable_T = typing.TypeVar('Deserializable_T', bound=Deserializable)


class DeserializableResolverByKeyChain:
    """decorator for base Deserializable class to add unified deserializer entrypoint feature."""
    def __init__(self, unique_key: str):
        self.unique_key = unique_key

    def __call__(self, master: type[Deserializable_T]) -> type[Deserializable_T]:
        if not inspect.isabstract(master):
            raise NotionDfValueError('master class must be abstract', {'master': master})

        master._subclass_by_keychain_dict = subclass_dict = FinalDict[Keychain, type[Deserializable]]()

        __init_subclass_prev__ = getattr(master, '__init_subclass__').__func__
        deserialize_prev = getattr(master, 'deserialize').__func__

        def __init_subclass__(cls: type[Deserializable_T], **kwargs) -> None:
            __init_subclass_prev__(cls, **kwargs)
            keychain = self.resolve_keychain(cls.get_mock_serialized())
            subclass_dict[keychain] = cls

        def _deserialize(cls: type[Deserializable_T], serialized: dict[str, Any]) -> Deserializable_T:
            if master != cls:
                return deserialize_prev(cls, serialized)
            keychain = self.resolve_keychain(serialized)
            if keychain not in subclass_dict:
                raise NotionDfValueError('cannot deserialize: unexpected type keychain',
                                         {'master': master, 'keychain': keychain})
            return subclass_dict[keychain].deserialize(serialized)

        setattr(master, '__init_subclass__', classmethod(__init_subclass__))
        setattr(master, 'deserialize', classmethod(_deserialize))
        return master

    def resolve_keychain(self, serialized: dict[str, Any]) -> Keychain:
        current_keychain = ()
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
            return Keychain(current_keychain)


resolve_by_keychain = DeserializableResolverByKeyChain
