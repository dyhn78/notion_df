from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, Any, NewType, Literal

from typing_extensions import Self

from notion_df.object.core import Deserializable, resolve_by_keychain
from notion_df.util.collection import StrEnum

UUID = NewType('UUID', str)
Timestamp = Literal['created_time', 'last_edited_time']


class Color(StrEnum):
    DEFAULT = 'default'
    GRAY = 'gray'
    BROWN = 'brown'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PURPLE = 'purple'
    PINK = 'pink'
    RED = 'red'


class TextColor(StrEnum):
    DEFAULT = 'default'
    GRAY = 'gray'
    BROWN = 'brown'
    ORANGE = 'orange'
    YELLOW = 'yellow'
    GREEN = 'green'
    BLUE = 'blue'
    PURPLE = 'purple'
    PINK = 'pink'
    RED = 'red'
    GRAY_BACKGROUND = 'gray_background'
    BROWN_BACKGROUND = 'brown_background'
    ORANGE_BACKGROUND = 'orange_background'
    YELLOW_BACKGROUND = 'yellow_background'
    GREEN_BACKGROUND = 'green_background'
    BLUE_BACKGROUND = 'blue_background'
    PURPLE_BACKGROUND = 'purple_background'
    PINK_BACKGROUND = 'pink_background'
    RED_BACKGROUND = 'red_background'


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
    AVERAGE = 'average'
    CHECKED = 'checked'
    COUNT = 'count'
    COUNT_PER_GROUP = 'count_per_group'
    COUNT_VALUES = 'count_values'
    DATE_RANGE = 'date_range'
    EARLIEST_DATE = 'earliest_date'
    EMPTY = 'empty'
    LATEST_DATE = 'latest_date'
    MAX = 'max'
    MEDIAN = 'median'
    MIN = 'min'
    NOT_EMPTY = 'not_empty'
    PERCENT_CHECKED = 'percent_checked'
    PERCENT_EMPTY = 'percent_empty'
    PERCENT_NOT_EMPTY = 'percent_not_empty'
    PERCENT_PER_GROUP = 'percent_per_group'
    PERCENT_UNCHECKED = 'percent_unchecked'
    RANGE = 'range'
    SHOW_ORIGINAL = 'show_original'
    SHOW_UNIQUE = 'show_unique'
    SUM = 'sum'
    UNCHECKED = 'unchecked'
    UNIQUE = 'unique'


@dataclass
class Annotations(Deserializable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: TextColor = TextColor.DEFAULT

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'bold': self.bold,
            'italic': self.italic,
            'strikethrough': self.strikethrough,
            'underline': self.underline,
            'code': self.code,
            'color': self.color
        }


@resolve_by_keychain('type')
class Icon(Deserializable, metaclass=ABCMeta):
    pass


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    value: str
    TYPE: ClassVar = 'emoji'

    def _plain_serialize(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }


@dataclass
class DateRange(Deserializable):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def _plain_serialize(self):
        return {
            'start': self.start,
            'end': self.end,
        }


@dataclass
class SelectOption(Deserializable):
    name: str
    id: str = field(init=False)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: Color = field(init=False)

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'name': self.name,
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars: Any) -> Self:
        plain_self = super()._plain_deserialize(serialized)
        plain_self.id = serialized['id']
        plain_self.color = serialized['color']
        return plain_self


@dataclass
class StatusGroups(Deserializable):
    name: str
    id: str = field(init=False)
    """Identifier of the option, which does not change if the name is changed. 
    These are sometimes, but not always, UUIDs."""
    color: Color = field(init=False)
    option_ids: list[str] = field()
    """Sorted list of ids of all options that belong to a group."""

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'name': self.name,
            'option_ids': self.option_ids,
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars: Any) -> Self:
        plain_self = super()._plain_deserialize(serialized)
        plain_self.id = serialized['id']
        plain_self.color = serialized['color']
        return plain_self
