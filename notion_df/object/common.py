from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, NewType, Iterable
from typing import Generic, Iterator, Optional, TypeVar

from typing_extensions import Self

from notion_df.core.serialization import DualSerializable, serialize_datetime, deserialize_datetime
from notion_df.object.constant import BlockColor, OptionColor
from notion_df.util.exception import NotionDfKeyError

UUID = NewType('UUID', str)
_VT = TypeVar('_VT')


@dataclass
class Property(DualSerializable, metaclass=ABCMeta):
    name: str = field(init=False, default=None)
    id: UUID = field(init=False, default=None)


Property_T = TypeVar('Property_T', bound=Property)


class Properties(DualSerializable, Generic[Property_T]):
    """the dict keys are same as each property's name or id (depending on request)"""
    by_id: dict[UUID, Property_T]
    by_name: dict[str, Property_T]

    def __init__(self, props: Iterable[Property_T] = ()):
        self.by_id = {}
        self.by_name = {}
        for prop in props:
            self.add(prop)

    def serialize(self) -> dict[str, Property_T]:
        return self.by_id

    @classmethod
    def _deserialize_this(cls, serialized: dict[UUID, Any]) -> Self:
        return cls(serialized.values())

    def __iter__(self) -> Iterator[Property_T]:
        return iter(self.by_id.values())

    def __getitem__(self, key: str | UUID | Property_T) -> Property_T:
        if isinstance(key, UUID):
            return self.by_id[key]
        if isinstance(key, str):
            return self.by_name[key]
        if isinstance(key, Property):
            return self.by_id[key.id]
        raise NotionDfKeyError(key)

    def __delitem__(self, key: str | UUID | Property_T) -> None:
        self.pop(self[key])

    def get(self, key: str | Property_T) -> Optional[Property_T]:
        try:
            return self[key]
        except KeyError:
            return None

    def add(self, prop: Property_T) -> None:
        self.by_id[prop.id] = prop
        self.by_name[prop.name] = prop

    def pop(self, prop: Property_T) -> Property_T:
        self.by_name.pop(prop.name)
        return self.by_id.pop(prop.id)


@dataclass
class Annotations(DualSerializable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: BlockColor = BlockColor.DEFAULT

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


icon_registry: dict[str, type[Icon]] = {}


class Icon(DualSerializable, metaclass=ABCMeta):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        if typename := cls.get_typename():
            icon_registry[typename] = cls

    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != Icon:
            return cls._deserialize_this(serialized)
        subclass = icon_registry[serialized['type']]
        return subclass.deserialize(serialized)


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    emoji: str

    @classmethod
    def get_typename(cls) -> str:
        return 'emoji'

    def serialize(self):
        return {
            "type": "emoji",
            "emoji": self.emoji
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['emoji'])


@dataclass
class DateRange(DualSerializable):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def serialize(self):
        return {
            'start': serialize_datetime(self.start),
            'end': serialize_datetime(self.end),
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(deserialize_datetime(serialized['start']), deserialize_datetime(serialized['end']))


@dataclass
class SelectOption(DualSerializable):
    name: str
    id: str = field(init=False)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: OptionColor = field(init=False)

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


@dataclass
class StatusGroups(DualSerializable):
    name: str
    id: str = field(init=False)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: OptionColor = field(init=False)
    option_ids: list[str] = field()
    """Sorted list of ids of all options that belong to a group."""

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)
