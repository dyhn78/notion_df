from __future__ import annotations

import inspect
import re
import types
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, InitVar
from datetime import datetime, date
from decimal import Decimal
from enum import Enum
from functools import cache
# noinspection PyUnresolvedReferences
from typing import Any, get_origin, get_args, final, NewType, cast, get_type_hints, _GenericAlias, Union, Literal, \
    TypeVar, overload
from uuid import UUID

import dateutil.parser
from typing_extensions import Self

from notion_df.util.exception import NotionDfValueError, NotionDfNotImplementedError, NotionDfTypeError
from notion_df.variable import my_tz


def serialize(obj: Any):
    """unified serializer for both Serializable and external classes."""
    if obj is None:
        return None
    if isinstance(obj, Serializable):
        return obj.serialize()
    if isinstance(obj, dict):
        return {k: serialize(v) for k, v in obj.items()}
    if isinstance(obj, list) or isinstance(obj, set):
        return [serialize(e) for e in obj]
    for typ in {bool, str, int, float}:
        if isinstance(obj, typ):
            return obj
    if isinstance(obj, Enum):
        return obj.value
    if isinstance(obj, date):
        return serialize_datetime(obj)
    if isinstance(obj, UUID):
        return str(obj)
    raise NotionDfValueError('cannot serialize', {'obj': obj})


T = TypeVar('T')


@overload
def deserialize(typ: type[T], serialized: Any) -> T:
    ...


@overload
def deserialize(typ: type, serialized: Any):
    ...


def deserialize(typ: type, serialized: Any):
    """unified deserializer for both Deserializable and external classes."""
    err_vars = {'typ': typ, 'serialized': serialized}
    typ_origin: type = get_origin(typ)
    typ_args = get_args(typ)

    # 0. explicitly unsupported values
    if typ is None or serialized is None:
        return serialized

    # 1. Non-class types
    if typ == Any:
        return serialized
    if type(typ) == NewType:
        typ_origin = cast(NewType, typ).__supertype__
        return typ(deserialize(typ_origin, serialized))
    if isinstance(typ, InitVar):  # TODO: is this really needed?
        return deserialize(typ.type, serialized)
    if typ_origin == Literal:
        if serialized in typ_args:
            return serialized
        raise NotionDfValueError('serialized value does not equal to any of Literal values', err_vars, linebreak=True)
    if isinstance(typ, types.UnionType) or typ_origin == Union:  # also can handle Optional
        for typ_arg in typ_args:
            try:
                return deserialize(typ_arg, serialized)
            except NotionDfValueError:
                pass
        raise NotionDfValueError('cannot deserialize to any of the UnionType', err_vars, linebreak=True)
    if isinstance(typ, types.GenericAlias) or isinstance(typ, _GenericAlias):
        err_vars.update({'typ.origin': typ_origin, 'typ.args': typ_args})
        try:
            if issubclass(typ_origin, dict):
                value_type = typ_args[1]
                return {k: deserialize(value_type, v) for k, v in serialized.items()}
            element_type = typ_args[0]
        except IndexError:
            raise NotionDfValueError('cannot deserialize: GenericAlias type with invalid args',
                                     err_vars, linebreak=True)
        if issubclass(typ_origin, list):
            return [deserialize(element_type, e) for e in serialized]
        if issubclass(typ_origin, set):
            return {deserialize(element_type, e) for e in serialized}
        raise NotionDfValueError('cannot deserialize: GenericAlias type with invalid origin',
                                 err_vars, linebreak=True)

    # 2. class types
    if not inspect.isclass(typ):
        raise NotionDfValueError('cannot deserialize: not supported type', err_vars, linebreak=True)
    if issubclass(typ, Deserializable):
        if isinstance(serialized, Deserializable):
            return serialized
        return typ.deserialize(serialized)
    if typ in {bool, str, int, float, Decimal} or issubclass(typ, Enum):
        try:
            return typ(serialized)
        except (ValueError, TypeError) as e:
            err_vars.update(exception=e)
            raise NotionDfValueError('cannot deserialize', err_vars, linebreak=True)
    if typ == UUID:
        if isinstance(serialized, UUID):
            return serialized
        return UUID(serialized)
    if issubclass(typ, datetime):
        try:
            return deserialize_datetime(serialized)
        except (ValueError, TypeError) as e:
            err_vars.update(exception=e)
            raise NotionDfValueError('cannot deserialize', err_vars, linebreak=True)
    raise NotionDfValueError('cannot deserialize: not supported class', err_vars, linebreak=True)


@dataclass
class Serializable(metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    can be dumped into JSON object."""

    @abstractmethod
    def serialize(self) -> Any:
        pass

    @final
    def _serialize_as_dict(self, **overrides: Any) -> dict[str, Any]:
        """helper method to implement serialize().
        Note: this drops post-init fields."""
        serialized = {}
        for fd in fields(self):
            if not fd.init:
                continue
            fd_value = overrides.get(fd.name, getattr(self, fd.name))
            serialized[fd.name] = serialize(fd_value)
        return serialized


@dataclass
class Deserializable(metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    can be loaded from JSON object."""

    @classmethod
    def deserialize(cls, serialized: Any) -> Self:
        """override this to allow proxy-deserialize of subclasses."""
        return cls._deserialize_this(serialized)

    @classmethod
    @abstractmethod
    def _deserialize_this(cls, serialized: Any) -> Self:
        """override this to modify deserialization of itself."""
        raise NotionDfNotImplementedError

    @classmethod
    @final
    def _deserialize_from_dict(cls, serialized: dict[str, Any], **overrides: Any) -> Self:
        """helper method to implement _deserialize_this(). must be called from a dataclass.
        Note: this collects post-init fields as well."""
        if inspect.isabstract(cls):
            raise NotionDfTypeError('cannot instantiate abstract class', {'cls': cls, 'serialized': serialized})

        def deserialize_field(fd_name: str):
            if fd_name in overrides:
                return overrides[fd_name]
            return deserialize(cls._get_type_hints()[fd_name], serialized[fd_name])

        init_params = {}
        for fd in fields(cls):
            if fd.init:
                init_params[fd.name] = deserialize_field(fd.name)
        self = cls(**init_params)  # type: ignore
        for fd in fields(cls):
            if not fd.init and (getattr(self, fd.name, None) is None) and fd.name in serialized:
                setattr(self, fd.name, deserialize_field(fd.name))
        return self

    @classmethod
    @cache
    def _get_type_hints(cls) -> dict[str, type]:
        return get_type_hints(cls)

    @final
    def _repr_non_default_fields(self):
        return (f'{type(self).__name__}('
                + ','.join(f'{fd.name}={getattr(self, fd.name)}' for fd in fields(self)
                           if getattr(self, fd.name) != fd.default)
                + ')')


class DualSerializable(Serializable, Deserializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable with JSON object.
    field with `init=False` are usually the case which not required from user-side but provided from server-side."""
    pass


def serialize_datetime(dt: date | datetime):
    if isinstance(dt, datetime):
        dt = dt.replace(tzinfo=my_tz).astimezone(my_tz)
    return dt.isoformat()


def deserialize_datetime(serialized: str) -> date | datetime:
    try:
        dt = dateutil.parser.parse(serialized)
    except dateutil.parser.ParserError as e:
        print(serialized)
        raise e
    if re.match(r'^\d{4}-\d{2}-\d{2}$', serialized):
        return dt.date()
    return dt.astimezone(my_tz)
