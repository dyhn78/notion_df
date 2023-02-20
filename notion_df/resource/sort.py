from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, Literal

from notion_df.resource.core import Serializable
from notion_df.resource.misc import Timestamp

Direction = Literal['ascending', 'descending']


class Sort(Serializable, metaclass=ABCMeta):
    pass


@dataclass
class PropertySort(Sort):
    property: str
    direction: Direction

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "property": self.property,
            "direction": self.direction
        }


@dataclass
class TimestampSort(Sort):
    timestamp: Timestamp
    direction: Direction

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "timestamp": self.timestamp,
            "direction": self.direction
        }
