from abc import ABCMeta
from dataclasses import dataclass
from typing import Literal, Any

from notion_df.object.core import Serializable
from notion_df.object.enum import TimestampType

Direction = Literal['ascending', 'descending']


class Sort(Serializable, metaclass=ABCMeta):
    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()


@dataclass
class PropertySort(Sort):
    property: str
    direction: Direction


@dataclass
class TimestampSort(Sort):
    timestamp_type: TimestampType
    direction: Direction
