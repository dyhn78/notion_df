from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, date
from typing import Any, Literal, Optional, TYPE_CHECKING, Iterator
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import DualSerializable
from notion_df.object.constant import BlockColor, OptionColor

if TYPE_CHECKING:
    from notion_df.core.entity import Entity


@dataclass
class PartialParent(DualSerializable):
    # https://developers.notion.com/reference/parent-object
    typename: Literal['database_id', 'page_id', 'block_id', 'workspace']
    id: Optional[UUID]

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.typename,
            self.typename: str(self.id) if self.id else None
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        typename = raw['type']
        if typename == 'workspace':
            return cls('workspace', None)
        parent_id = UUID(raw[typename])
        return cls(typename, parent_id)

    @property
    def entity(self) -> Optional[Entity]:
        from notion_df.entity import Block, Database, Page

        match self.typename:
            case 'block_id':
                return Block(self.id)
            case 'database_id':
                return Database(self.id)
            case 'page_id':
                return Page(self.id)
            case 'workspace':
                return None


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
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw)

    def __repr__(self):
        # repr() only non-default fields
        return self._repr_non_default_fields()


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
    def deserialize(cls, raw: dict[str, Any]) -> Self:
        if cls != Icon:
            return cls._deserialize_this(raw)
        subclass = icon_registry[raw['type']]
        return subclass.deserialize(raw)


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    value: str

    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.value})'

    def __str__(self) -> str:
        return self.value

    @classmethod
    def get_typename(cls) -> str:
        return 'emoji'

    def serialize(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw['emoji'])


@dataclass
class DateRange(DualSerializable):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: date | datetime
    end: date | datetime

    def __iter__(self) -> Iterator[date | datetime]:
        return iter([self.start, self.end])

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw)


@dataclass
class SelectOption(DualSerializable):
    name: str
    id: str = field(init=False, default=None)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: OptionColor = field(init=False, default=None)

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw)

    def __eq__(self, other: SelectOption | str) -> bool:
        """compare with str to match the name or id."""
        if isinstance(other, SelectOption):
            if self.id != other.id and self.id is not None and other.id is not None:
                return False
            if self.color != other.color and self.color is not None and other.color is not None:
                return False
            return self.name == other.name
        if isinstance(other, str):
            return self.name == other or self.id == other


class SelectOptions(list[SelectOption]):
    def __init__(self, select_options: list[SelectOption]):
        super().__init__(select_options)


@dataclass
class StatusGroups(DualSerializable):
    name: str
    id: str = field(init=False, default=None)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: OptionColor = field(init=False, default=None)
    option_ids: list[str] = field()
    """Sorted list of ids of all options that belong to a group."""

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw)

    def __eq__(self, other: StatusGroups) -> bool:
        if self.id != other.id and self.id is not None and other.id is not None:
            return False
        return self.name == other.name and self.option_ids == other.option_ids
