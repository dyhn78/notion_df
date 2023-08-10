from abc import ABCMeta
from dataclasses import dataclass
from typing import Literal, Any

from notion_df.core.serialization import Serializable
from notion_df.data.constant import TimestampName

Direction = Literal['ascending', 'descending']


class Sort(Serializable, metaclass=ABCMeta):
    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()


@dataclass
class PropertySort(Sort):
    property: str
    direction: Direction


@dataclass
class TimestampSort(Sort):
    timestamp_type: TimestampName
    direction: Direction

    def serialize(self) -> dict[str, Any]:
        return {
            'timestamp': self.timestamp_type,
            'direction': self.direction,
        }
