from abc import ABCMeta
from dataclasses import dataclass
from typing import Literal

from notion_df.response.core import Serializable
from notion_df.response.misc import Timestamp

Direction = Literal['ascending', 'descending']


class Sort(Serializable, metaclass=ABCMeta):
    pass


@dataclass
class PropertySort(Sort):
    property: str
    direction: Direction


@dataclass
class TimestampSort(Sort):
    timestamp: Timestamp
    direction: Direction
