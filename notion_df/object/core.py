from __future__ import annotations

import inspect
import types
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, fields, InitVar, Field
from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import Any, get_origin, get_args, final

import dateutil.parser
from typing_extensions import Self

from notion_df.util.exception import NotionDfValueError, NotionDfNotImplementedError
from notion_df.variable import Variables


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
        return serialize_datetime(obj)
    raise NotionDfValueError('cannot serialize', {'obj': obj})


def deserialize(typ: type, serialized: Any):
    """unified deserializer for both Deserializable and external classes."""
    err_vars = {'typ': typ, 'serialized': serialized}
    typ_origin: type = get_origin(typ)
    typ_args = get_args(typ)

    # 1. Non-class types
    if isinstance(typ, types.GenericAlias):
        err_vars.update({'typ.origin': typ_origin, 'typ.args': typ_args})
        try:
            if issubclass(typ_origin, dict):
                value_type = typ_args[1]
                return {k: deserialize(value_type, v) for k, v in serialized.items()}
            element_type = typ_args[0]
            if issubclass(typ_origin, list):
                return [deserialize(element_type, e) for e in serialized]
            if issubclass(typ_origin, set):
                return {deserialize(element_type, e) for e in serialized}
            raise NotionDfValueError('cannot deserialize: GenericAlias type with invalid origin', err_vars)
        except IndexError:
            raise NotionDfValueError('cannot deserialize: GenericAlias type with invalid args', err_vars)
    if isinstance(typ, types.UnionType):  # also can handle Optional
        for typ_arg in typ_args:
            try:
                return deserialize(typ_arg, serialized)
            except NotionDfValueError:
                pass
        raise NotionDfValueError('cannot deserialize to any of the UnionType', err_vars)

    # 2. class types
    if not inspect.isclass(typ):
        raise NotionDfValueError('cannot deserialize: not supported type', err_vars)
    if issubclass(typ, Deserializable):
        return typ.deserialize(serialized)
    if typ in {bool, str, int, float, Decimal}:
        if type(serialized) != typ:
            raise NotionDfValueError('cannot deserialize: type(serialized) != typ', err_vars)
        return serialized
    if issubclass(typ, Enum):
        return typ(serialized)
    if issubclass(typ, datetime):
        return deserialize_datetime(serialized)
    if isinstance(typ, InitVar):  # TODO: is this really needed?
        return deserialize(typ.type, serialized)
    raise NotionDfValueError('cannot deserialize: not supported class', err_vars)


@dataclass
class Serializable(metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    can be dumped into JSON object."""
    @abstractmethod
    def serialize(self) -> dict[str, Any]:
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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        """override this to allow proxy-deserialize of subclasses."""
        return cls._deserialize_this(serialized)

    @classmethod
    @abstractmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        """override this to modify deserialization of itself."""
        raise NotionDfNotImplementedError

    @classmethod
    @final
    def _deserialize_from_dict(cls, serialized: dict[str, Any], **overrides: Any) -> Self:
        """helper method to implement _deserialize_this().
        Note: this collects post-init fields as well."""

        def deserialize_field(fd: Field):
            return deserialize(fd.type, serialized[fd.name])

        serialized.update(overrides)
        self = cls(**{fd.name: deserialize_field(fd) for fd in fields(cls) if fd.init})  # type: ignore
        for fd in fields(cls):
            if not fd.init:
                setattr(self, fd.name, deserialize_field(fd))
        return self


class DualSerializable(Serializable, Deserializable, metaclass=ABCMeta):
    """dataclass representation of the resources defined in Notion REST API.
    interchangeable with JSON object."""
    pass


def serialize_datetime(dt: datetime):
    return dt.astimezone(Variables.timezone).isoformat()


def deserialize_datetime(serialized: str):
    datetime_obj = dateutil.parser.parse(serialized)
    return datetime_obj.astimezone(Variables.timezone)
