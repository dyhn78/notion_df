from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypeVar, Callable, Union, Generic, Any
from uuid import UUID

from notion_df.core.serialization import Serializable, serialize
from notion_df.object.constant import TimestampType

CompoundOperatorType = Literal['and', 'or']
RollupAggregateType = Literal['any', 'every', 'none']
FilterPredicate = dict[str, Any]


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


@dataclass
class FilterType:
    filter_predicate: dict[str, Any]

    @abstractmethod
    def serialize_filter(self, name_or_id: str | UUID) -> dict[str, Any]:
        pass


FilterType_T = TypeVar('FilterType_T', bound=FilterType)


class FilterTypeBuilder(Generic[FilterType_T], metaclass=ABCMeta):
    def __init__(self, get_filter_type: Callable[[FilterPredicate], FilterType_T]):
        self._get_filter_type = get_filter_type


@dataclass
class PropertyFilterType(FilterType):
    # https://developers.notion.com/reference/post-database-query-filter
    filter_predicate: FilterPredicate
    property_type: str

    def serialize_filter(self, name_or_id: str | UUID):
        return {
            "property": name_or_id,
            self.property_type: serialize(self.filter_predicate)
        }


@dataclass
class RollupAggregateFilterType(PropertyFilterType):
    aggregate_type: RollupAggregateType

    def serialize_filter(self, name_or_id: str | UUID):
        return {
            "property": name_or_id,
            "rollup": {
                self.aggregate_type: {
                    self.property_type: serialize(self.filter_predicate)
                }
            }
        }

    def serialize_filter_2(self, name_or_id: str | UUID):
        # TODO: find which is correct by actual testing
        return {
            "property": name_or_id,
            self.aggregate_type: {
                self.property_type: serialize(self.filter_predicate)
            }
        }


@dataclass
class TimestampFilterType(FilterType):
    filter_predicate: FilterPredicate

    def serialize_filter(self, timestamp_type: TimestampType):
        return {
            "timestamp_type": timestamp_type,
            timestamp_type: serialize(self.filter_predicate)
        }


class TextFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ["title", "rich_text", "url", "email", and "phone_number"]"""

    def equals(self, value: str) -> FilterType_T:
        return self._get_filter_type({'equals': value})

    def does_not_equal(self, value: str) -> FilterType_T:
        return self._get_filter_type({'does_not_equal': value})

    def contains(self, value: str) -> FilterType_T:
        return self._get_filter_type({'contains': value})

    def does_not_contain(self, value: str) -> FilterType_T:
        return self._get_filter_type({'does_not_contain': value})

    def starts_with(self, value: str) -> FilterType_T:
        return self._get_filter_type({'starts_with': value})

    def ends_with(self, value: str) -> FilterType_T:
        return self._get_filter_type({'ends_with': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class NumberFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ['number']"""

    def equals(self, value: Union[int, Decimal]) -> FilterType_T:
        return self._get_filter_type({'equals': value})

    def does_not_equal(self, value: Union[int, Decimal]) -> FilterType_T:
        return self._get_filter_type({'does_not_equal': value})

    def greater_than(self, value: Union[int, Decimal]) -> FilterType_T:
        return self._get_filter_type({'greater_than': value})

    def less_than(self, value: Union[int, Decimal]) -> FilterType_T:
        return self._get_filter_type({'less_than': value})

    def greater_than_or_equal_to(self, value: Union[int, Decimal]) -> FilterType_T:
        return self._get_filter_type({'greater_than_or_equal_to': value})

    def less_than_or_equal_to(self, value: Union[int, Decimal]) -> FilterType_T:
        return self._get_filter_type({'less_than_or_equal_to': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class CheckboxFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ['checkbox']"""

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class SelectFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ['select', 'status']"""

    def equals(self, value: str) -> FilterType_T:
        return self._get_filter_type({'equals': value})

    def does_not_equal(self, value: str) -> FilterType_T:
        return self._get_filter_type({'does_not_equal': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class MultiSelectFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ['multi_select']"""

    def contains(self, value: str) -> FilterType_T:
        return self._get_filter_type({'contains': value})

    def does_not_contain(self, value: str) -> FilterType_T:
        return self._get_filter_type({'does_not_contain': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class DateFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ["date", "created_time", "last_edited_time"]"""

    def equals(self, value: datetime) -> FilterType_T:
        return self._get_filter_type({'equals': value})

    def before(self, value: datetime) -> FilterType_T:
        return self._get_filter_type({'before': value})

    def after(self, value: datetime) -> FilterType_T:
        return self._get_filter_type({'after': value})

    def on_or_before(self, value: datetime) -> FilterType_T:
        return self._get_filter_type({'on_or_before': value})

    def on_or_after(self, value: datetime) -> FilterType_T:
        return self._get_filter_type({'on_or_after': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})

    def past_week(self) -> FilterType_T:
        return self._get_filter_type({'past_week': {}})

    def past_month(self) -> FilterType_T:
        return self._get_filter_type({'past_month': {}})

    def past_year(self) -> FilterType_T:
        return self._get_filter_type({'past_year': {}})

    def next_week(self) -> FilterType_T:
        return self._get_filter_type({'next_week': {}})

    def next_month(self) -> FilterType_T:
        return self._get_filter_type({'next_month': {}})

    def next_year(self) -> FilterType_T:
        return self._get_filter_type({'next_year': {}})


class PeopleFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ["people", "created_by", and "last_edited_by"]"""

    def contains(self, value: str) -> FilterType_T:
        return self._get_filter_type({'contains': value})

    def does_not_contain(self, value: str) -> FilterType_T:
        return self._get_filter_type({'does_not_contain': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class FilesFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ['files']"""

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})


class RelationFilterTypeBuilder(FilterTypeBuilder[FilterType_T]):
    """eligible property types: ['relation']"""

    def contains(self, value: UUID) -> FilterType_T:
        return self._get_filter_type({'contains': value})

    def does_not_contain(self, value: UUID) -> FilterType_T:
        return self._get_filter_type({'does_not_contain': value})

    def is_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_empty': True})

    def is_not_empty(self) -> FilterType_T:
        return self._get_filter_type({'is_not_empty': True})
