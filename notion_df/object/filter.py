from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypeVar, Union, Any
from uuid import UUID

from typing_extensions import Self

from notion_df.object.constant import TimestampName
from notion_df.util.serialization import Serializable, serialize

CompoundOperator = Literal['and', 'or']
RollupAggregate = Literal['any', 'every', 'none']
FilterCondition = dict[str, Any]


@dataclass
class Filter(Serializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/post-database-query-filter
    def __and__(self, other: Filter) -> CompoundFilter:
        return self.__compound(other, 'and')

    def __or__(self, other: Filter) -> CompoundFilter:
        return self.__compound(other, 'or')

    def __compound(self, other: Filter, operator: CompoundOperator) -> CompoundFilter:
        if isinstance(self, CompoundFilter) and self.operator == operator:
            if isinstance(other, CompoundFilter) and other.operator == operator:
                return CompoundFilter(operator, self.elements + other.elements)
            return CompoundFilter(operator, self.elements + [other])
        if isinstance(other, CompoundFilter) and other.operator == operator:
            return CompoundFilter(operator, [self] + other.elements)
        return CompoundFilter(operator, [self, other])


@dataclass
class CompoundFilter(Filter):
    operator: CompoundOperator
    elements: list[Filter]

    def serialize(self):
        return {self.operator: serialize(self.elements)}


@dataclass
class PropertyFilter(Filter):
    name_or_id: str | UUID
    type: FilterType

    def serialize(self):
        return {
            "property": self.name_or_id,
            self.type.get_typename(): serialize(self.type.condition)
        }


@dataclass
class RollupPropertyAggregateFilter(Filter):
    name_or_id: str | UUID
    aggregate_type: RollupAggregate
    type: FilterType

    def serialize(self):
        return {
            "property": self.name_or_id,
            "rollup": {
                self.aggregate_type: {
                    self.type.get_typename(): serialize(self.type.condition)
                }
            }
        }

    def serialize2(self):
        # TODO: find which is correct by actual testing
        return {
            "property": self.name_or_id,
            self.aggregate_type: {
                self.type.get_typename(): serialize(self.type.condition)
            }
        }


@dataclass
class TimestampFilter(Filter):
    name: TimestampName
    type: FilterType

    def serialize(self):
        return {
            "timestamp_type": self.name,
            self.name: serialize(self.type.condition)
        }


@dataclass
class FilterType(metaclass=ABCMeta):
    condition: FilterCondition

    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass


FilterType_T = TypeVar('FilterType_T', bound=FilterType)


class TextFilterType(FilterType):
    """eligible property types: ["title", "rich_text", "url", "email", and "phone_number"]"""

    @classmethod
    def get_typename(cls) -> str:
        return 'text'

    @classmethod
    def equals(cls, value: str) -> Self:
        return cls({'equals': value})

    @classmethod
    def does_not_equal(cls, value: str) -> Self:
        return cls({'does_not_equal': value})

    @classmethod
    def contains(cls, value: str) -> Self:
        return cls({'contains': value})

    @classmethod
    def does_not_contain(cls, value: str) -> Self:
        return cls({'does_not_contain': value})

    @classmethod
    def starts_with(cls, value: str) -> Self:
        return cls({'starts_with': value})

    @classmethod
    def ends_with(cls, value: str) -> Self:
        return cls({'ends_with': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class NumberFilterType(FilterType):
    """eligible property types: ['number']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'number'

    @classmethod
    def equals(cls, value: Union[int, Decimal]) -> Self:
        return cls({'equals': value})

    @classmethod
    def does_not_equal(cls, value: Union[int, Decimal]) -> Self:
        return cls({'does_not_equal': value})

    @classmethod
    def greater_than(cls, value: Union[int, Decimal]) -> Self:
        return cls({'greater_than': value})

    @classmethod
    def less_than(cls, value: Union[int, Decimal]) -> Self:
        return cls({'less_than': value})

    @classmethod
    def greater_than_or_equal_to(cls, value: Union[int, Decimal]) -> Self:
        return cls({'greater_than_or_equal_to': value})

    @classmethod
    def less_than_or_equal_to(cls, value: Union[int, Decimal]) -> Self:
        return cls({'less_than_or_equal_to': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class CheckboxFilterType(FilterType):
    """eligible property types: ['checkbox']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'checkbox'

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class SelectFilterType(FilterType):
    """eligible property types: ['select', 'status']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'select'

    @classmethod
    def equals(cls, value: str) -> Self:
        return cls({'equals': value})

    @classmethod
    def does_not_equal(cls, value: str) -> Self:
        return cls({'does_not_equal': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class MultiSelectFilterType(FilterType):
    """eligible property types: ['multi_select']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'multi_select'

    @classmethod
    def contains(cls, value: str) -> Self:
        return cls({'contains': value})

    @classmethod
    def does_not_contain(cls, value: str) -> Self:
        return cls({'does_not_contain': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class DateFilterType(FilterType):
    """eligible property types: ["date", "created_time", "last_edited_time"]"""

    @classmethod
    def get_typename(cls) -> str:
        return 'date'

    @classmethod
    def equals(cls, value: datetime) -> Self:
        return cls({'equals': value})

    @classmethod
    def before(cls, value: datetime) -> Self:
        return cls({'before': value})

    @classmethod
    def after(cls, value: datetime) -> Self:
        return cls({'after': value})

    @classmethod
    def on_or_before(cls, value: datetime) -> Self:
        return cls({'on_or_before': value})

    @classmethod
    def on_or_after(cls, value: datetime) -> Self:
        return cls({'on_or_after': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})

    @classmethod
    def past_week(cls) -> Self:
        return cls({'past_week': {}})

    @classmethod
    def past_month(cls) -> Self:
        return cls({'past_month': {}})

    @classmethod
    def past_year(cls) -> Self:
        return cls({'past_year': {}})

    @classmethod
    def next_week(cls) -> Self:
        return cls({'next_week': {}})

    @classmethod
    def next_month(cls) -> Self:
        return cls({'next_month': {}})

    @classmethod
    def next_year(cls) -> Self:
        return cls({'next_year': {}})


class PeopleFilterType(FilterType):
    """eligible property types: ["people", "created_by", and "last_edited_by"]"""

    @classmethod
    def get_typename(cls) -> str:
        return 'people'

    @classmethod
    def contains(cls, value: str) -> Self:
        return cls({'contains': value})

    @classmethod
    def does_not_contain(cls, value: str) -> Self:
        return cls({'does_not_contain': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class FilesFilterType(FilterType):
    """eligible property types: ['files']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'files'

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})


class RelationFilterType(FilterType):
    """eligible property types: ['relation']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'relation'

    @classmethod
    def contains(cls, value: UUID) -> Self:
        return cls({'contains': value})

    @classmethod
    def does_not_contain(cls, value: UUID) -> Self:
        return cls({'does_not_contain': value})

    @classmethod
    def is_empty(cls) -> Self:
        return cls({'is_empty': True})

    @classmethod
    def is_not_empty(cls) -> Self:
        return cls({'is_not_empty': True})
