from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Any, NewType, Literal

from notion_df.resource.core import TypedResource, Deserializable
from notion_df.util.collection import StrEnum

UUID = NewType('UUID', str)
Timestamp = Literal['created_time', 'last_edited_time']


class Color(StrEnum):
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


class TextColor(StrEnum):
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
class Annotations(Deserializable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: TextColor = TextColor.default

    def plain_serialize(self) -> dict[str, Any]:
        return {
            'bold': self.bold,
            'italic': self.italic,
            'strikethrough': self.strikethrough,
            'underline': self.underline,
            'code': self.code,
            'color': self.color
        }


class Icon(TypedResource, metaclass=ABCMeta):
    pass


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    value: str
    TYPE: ClassVar = 'emoji'

    def plain_serialize(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }


@dataclass
class DateRange(Deserializable):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def plain_serialize(self):
        return {
            'start': self.start,
            'end': self.end,
        }


@dataclass
class SelectOption(Deserializable):
    name: str
    id: str = field()
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: Color

    def plain_serialize(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'id': self.id,
            'color': self.color
        }


@dataclass
class StatusGroups(Deserializable):
    name: str
    id: str = field()
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: Color
    option_ids: list[str] = field()
    """Sorted list of ids of all options that belong to a group."""

    def plain_serialize(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'id': self.id,
            'color': self.color
        }


class NumberFormat(StrEnum):
    NUMBER = 'number'
    NUMBER_WITH_COMMAS = 'number_with_commas'
    PERCENT = 'percent'
    DOLLAR = 'dollar'
    CANADIAN_DOLLAR = 'canadian_dollar'
    EURO = 'euro'
    POUND = 'pound'
    YEN = 'yen'
    RUBLE = 'ruble'
    RUPEE = 'rupee'
    WON = 'won'
    YUAN = 'yuan'
    REAL = 'real'
    LIRA = 'lira'
    RUPIAH = 'rupiah'
    FRANC = 'franc'
    HONG_KONG_DOLLAR = 'hong_kong_dollar'
    NEW_ZEALAND_DOLLAR = 'new_zealand_dollar'
    KRONA = 'krona'
    NORWEGIAN_KRONE = 'norwegian_krone'
    MEXICAN_PESO = 'mexican_peso'
    RAND = 'rand'
    NEW_TAIWAN_DOLLAR = 'new_taiwan_dollar'
    DANISH_KRONE = 'danish_krone'
    ZLOTY = 'zloty'
    BAHT = 'baht'
    FORINT = 'forint'
    KORUNA = 'koruna'
    SHEKEL = 'shekel'
    CHILEAN_PESO = 'chilean_peso'
    PHILIPPINE_PESO = 'philippine_peso'
    DIRHAM = 'dirham'
    COLOMBIAN_PESO = 'colombian_peso'
    RIYAL = 'riyal'
    RINGGIT = 'ringgit'
    LEU = 'leu'
    ARGENTINE_PESO = 'argentine_peso'
    URUGUAYAN_PESO = 'uruguayan_peso'
    SINGAPORE_DOLLAR = 'singapore_dollar'


class RollupFunction(StrEnum):
    COUNT = 'count'
    COUNT_VALUES = 'count_values'
    EMPTY = 'empty'
    NOT_EMPTY = 'not_empty'
    UNIQUE = 'unique'
    SHOW_UNIQUE = 'show_unique'
    PERCENT_EMPTY = 'percent_empty'
    PERCENT_NOT_EMPTY = 'percent_not_empty'
    SUM = 'sum'
    AVERAGE = 'average'
    MEDIAN = 'median'
    MIN = 'min'
    MAX = 'max'
    RANGE = 'range'
    EARLIEST_DATE = 'earliest_date'
    LATEST_DATE = 'latest_date'
    DATE_RANGE = 'date_range'
    CHECKED = 'checked'
    UNCHECKED = 'unchecked'
    PERCENT_CHECKED = 'percent_checked'
    PERCENT_UNCHECKED = 'percent_unchecked'
    COUNT_PER_GROUP = 'count_per_group'
    PERCENT_PER_GROUP = 'percent_per_group'
    SHOW_ORIGINAL = 'show_original'
