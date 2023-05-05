from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypeVar, Callable, Union, Generic
from uuid import UUID

from notion_df.core.serialization import Serializable, serialize
from notion_df.object.constant import TimestampType

_T = TypeVar('_T')
CompoundOperatorType = Literal['and', 'or']
AggregateType = Literal['any', 'every', 'none']


@dataclass
class Filter(Serializable, metaclass=ABCMeta):
    def __and__(self, other: Filter) -> CompoundFilter:
        return self.__compound(other, 'and')

    def __or__(self, other: Filter) -> CompoundFilter:
        return self.__compound(other, 'or')

    def __compound(self, other: Filter, operator: CompoundOperatorType) -> CompoundFilter:
        if isinstance(self, CompoundFilter) and self.operator == operator:
            if isinstance(other, CompoundFilter) and other.operator == operator:
                return CompoundFilter(operator, self.elements + other.elements)
            return CompoundFilter(operator, self.elements + [other])
        if isinstance(other, CompoundFilter) and other.operator == operator:
            return CompoundFilter(operator, [self] + other.elements)
        return CompoundFilter(operator, [self, other])


@dataclass
class CompoundFilter(Filter):
    operator: CompoundOperatorType
    elements: list[Filter]

    def serialize(self):
        return {self.operator: serialize(self.elements)}


Filter_T = TypeVar('Filter_T', bound=Filter)


class FilterPredicate(Generic[Filter_T], metaclass=ABCMeta):
    def __init__(self, filter_builder: Callable[[dict], Filter_T]):
        self._init_filter = filter_builder


FilterPredicate_T = TypeVar('FilterPredicate_T', bound=FilterPredicate)


@dataclass
class PropertyFilter(Filter):
    # https://developers.notion.com/reference/post-database-query-filter
    filter_type: dict
    property_name: str
    property_type: str

    def serialize(self):
        return {
            "property": self.property_name,
            self.property_type: serialize(self.filter_type)
        }


@dataclass
class ArrayRollupFilter(PropertyFilter):
    aggregate_type: AggregateType

    def serialize(self):
        return {
            "property": self.property_name,
            "rollup": {
                self.aggregate_type: {
                    self.property_type: serialize(self.filter_type)
                }
            }
        }

    def serialize_2(self):
        # TODO: find which is correct by actual testing
        return {
            "property": self.property_name,
            self.aggregate_type: {
                self.property_type: serialize(self.filter_type)
            }
        }


def get_array_rollup_filter_predicate(property_name: str, property_type: str, aggregate_type: AggregateType):
    return FilterPredicate(lambda filter_type: ArrayRollupFilter(
        filter_type, property_name, property_type, aggregate_type))


@dataclass
class TimestampFilter(Filter):
    filter_type: dict
    timestamp_type: TimestampType

    def serialize(self):
        return {
            "timestamp_type": self.timestamp_type,
            self.timestamp_type: serialize(self.filter_type)
        }


def get_timestamp_filter_predicate(timestamp_type: TimestampType):
    return FilterPredicate(lambda filter_type: TimestampFilter(filter_type, timestamp_type))


class TextFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ["title", "rich_text", "url", "email", and "phone_number"]"""

    def equals(self, value: str) -> Filter_T:
        return self._init_filter({'equals': value})

    def does_not_equal(self, value: str) -> Filter_T:
        return self._init_filter({'does_not_equal': value})

    def contains(self, value: str) -> Filter_T:
        return self._init_filter({'contains': value})

    def does_not_contain(self, value: str) -> Filter_T:
        return self._init_filter({'does_not_contain': value})

    def starts_with(self, value: str) -> Filter_T:
        return self._init_filter({'starts_with': value})

    def ends_with(self, value: str) -> Filter_T:
        return self._init_filter({'ends_with': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class NumberFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ['number']"""

    def equals(self, value: Union[int, Decimal]) -> Filter_T:
        return self._init_filter({'equals': value})

    def does_not_equal(self, value: Union[int, Decimal]) -> Filter_T:
        return self._init_filter({'does_not_equal': value})

    def greater_than(self, value: Union[int, Decimal]) -> Filter_T:
        return self._init_filter({'greater_than': value})

    def less_than(self, value: Union[int, Decimal]) -> Filter_T:
        return self._init_filter({'less_than': value})

    def greater_than_or_equal_to(self, value: Union[int, Decimal]) -> Filter_T:
        return self._init_filter({'greater_than_or_equal_to': value})

    def less_than_or_equal_to(self, value: Union[int, Decimal]) -> Filter_T:
        return self._init_filter({'less_than_or_equal_to': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class CheckboxFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ['checkbox']"""

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class SelectFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ['select', 'status']"""

    def equals(self, value: str) -> Filter_T:
        return self._init_filter({'equals': value})

    def does_not_equal(self, value: str) -> Filter_T:
        return self._init_filter({'does_not_equal': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class MultiSelectFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ['multi_select']"""

    def contains(self, value: str) -> Filter_T:
        return self._init_filter({'contains': value})

    def does_not_contain(self, value: str) -> Filter_T:
        return self._init_filter({'does_not_contain': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class DateFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ["date", "created_time", "last_edited_time"]"""

    def equals(self, value: datetime) -> Filter_T:
        return self._init_filter({'equals': value})

    def before(self, value: datetime) -> Filter_T:
        return self._init_filter({'before': value})

    def after(self, value: datetime) -> Filter_T:
        return self._init_filter({'after': value})

    def on_or_before(self, value: datetime) -> Filter_T:
        return self._init_filter({'on_or_before': value})

    def on_or_after(self, value: datetime) -> Filter_T:
        return self._init_filter({'on_or_after': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})

    def past_week(self) -> Filter_T:
        return self._init_filter({'past_week': {}})

    def past_month(self) -> Filter_T:
        return self._init_filter({'past_month': {}})

    def past_year(self) -> Filter_T:
        return self._init_filter({'past_year': {}})

    def next_week(self) -> Filter_T:
        return self._init_filter({'next_week': {}})

    def next_month(self) -> Filter_T:
        return self._init_filter({'next_month': {}})

    def next_year(self) -> Filter_T:
        return self._init_filter({'next_year': {}})


class PeopleFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ["people", "created_by", and "last_edited_by"]"""

    def contains(self, value: str) -> Filter_T:
        return self._init_filter({'contains': value})

    def does_not_contain(self, value: str) -> Filter_T:
        return self._init_filter({'does_not_contain': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class FilesFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ['files']"""

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})


class RelationFilterPredicate(FilterPredicate[Filter_T]):
    """eligible property types: ['relation']"""

    def contains(self, value: UUID) -> Filter_T:
        return self._init_filter({'contains': value})

    def does_not_contain(self, value: UUID) -> Filter_T:
        return self._init_filter({'does_not_contain': value})

    def is_empty(self) -> Filter_T:
        return self._init_filter({'is_empty': True})

    def is_not_empty(self) -> Filter_T:
        return self._init_filter({'is_not_empty': True})
