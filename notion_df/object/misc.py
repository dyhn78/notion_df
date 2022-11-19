from __future__ import annotations as __

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from enum import Enum

from notion_df.blueprint.create_a_database import Dictable


@dataclass
class Emoji(Dictable):
    value: str

    def to_dict(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }


@dataclass
class File(Dictable, metaclass=ABCMeta):
    pass


@dataclass
class InternalFile(File):
    url: str
    expiry_time: datetime

    def to_dict(self):
        return {
            "type": "file",
            "file": {
                "url": self.url,
                "expiry_time": self.expiry_time.isoformat()
            }
        }


@dataclass
class ExternalFile(File):
    url: str

    def to_dict(self):
        return {
            "type": "external",
            "external": {
                "url": self.url
            }
        }


class Color(Enum):
    default = 'default'
    gray = 'gray'
    brown = 'brown'
    orange = 'orange'
    yellow = 'yellow'
    green = 'green'
    blue = 'blue'
    purple = 'purple'
    pink = 'pink'
    red = 'red'
    gray_background = 'gray_background'
    brown_background = 'brown_background'
    orange_background = 'orange_background'
    yellow_background = 'yellow_background'
    green_background = 'green_background'
    blue_background = 'blue_background'
    purple_background = 'purple_background'
    pink_background = 'pink_background'
    red_background = 'red_background'


@dataclass
class Annotations(Dictable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: Color | str = Color.default

    def to_dict(self):
        return {
            'bold': self.bold,
            'italic': self.italic,
            'strikethrough': self.strikethrough,
            'underline': self.underline,
            'code': self.code,
            'color': Color(self.color).value
        }
