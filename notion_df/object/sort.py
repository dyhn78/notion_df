from abc import ABCMeta
from dataclasses import dataclass
from typing import Literal, Any

from notion_df.object.constant import TimestampName
from notion_df.util.serialization import Serializable

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
