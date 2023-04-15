from abc import ABCMeta
from dataclasses import dataclass
from typing import Literal

from notion_df.response.core import AsDictSerializable
from notion_df.response.misc import TimestampType

Direction = Literal['ascending', 'descending']


class Sort(AsDictSerializable, metaclass=ABCMeta):
    pass


@dataclass
class PropertySort(Sort):
    property: str
    direction: Direction


@dataclass
class TimestampSort(Sort):
    timestamp_type: TimestampType
    direction: Direction
