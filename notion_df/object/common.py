from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, NewType, final

from typing_extensions import Self

from notion_df.object.constant import BlockColor, OptionColor
from notion_df.object.core import DualSerializable, serialize_datetime, deserialize_datetime

UUID = NewType('UUID', str)


@dataclass
class Annotations(DualSerializable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: BlockColor = BlockColor.DEFAULT

    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_fromdict(serialized)


icon_registry: dict[str, type[Icon]] = {}


class Icon(DualSerializable, metaclass=ABCMeta):
    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        icon_registry[cls.get_type()] = cls

    @classmethod
    @abstractmethod
    def get_type(cls) -> str:
        pass

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != Icon:
            return cls._deserialize_this(serialized)
        subclass = icon_registry[cls.get_type()]
        return subclass._deserialize_this(serialized)


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    emoji: str

    @classmethod
    def get_type(cls) -> str:
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
        return self._serialize_asdict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_fromdict(serialized)


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
        return self._serialize_asdict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_fromdict(serialized)
