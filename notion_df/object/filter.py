from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypeVar, Generic, Optional, Callable, overload, NewType
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import Serializable, serialize
from notion_df.object.constant import TimestampType

_T = TypeVar('_T')
FilterType = NewType('FilterType', dict)
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


class FilterBuilder(metaclass=ABCMeta):
    def __init__(self, init_filter: Callable[[FilterType], Filter]):
        self.init_filter = init_filter


@dataclass
class PropertyFilter(Filter):
    # https://developers.notion.com/reference/post-database-query-filter
    filter_type: FilterType
    property_name: str
    property_type: str

    def serialize(self):
        return {
            "property": self.property_name,
            self.property_type: serialize(self.filter_type)
        }


def get_property_filter_builder(property_name: str, property_type: str):
    return FilterBuilder(lambda filter_type: PropertyFilter(filter_type, property_name, property_type))


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


def get_array_rollup_filter_builder(property_name: str, property_type: str, aggregate_type: AggregateType):
    return FilterBuilder(lambda filter_type: ArrayRollupFilter(
        filter_type, property_name, property_type, aggregate_type))


@dataclass
class TimestampFilter(Filter):
    filter_type: FilterType
    timestamp_type: TimestampType

    def serialize(self):
        return {
            "timestamp_type": self.timestamp_type,
            self.timestamp_type: serialize(self.filter_type)
        }


def get_timestamp_filter_builder(timestamp_type: TimestampType):
    return FilterBuilder(lambda filter_type: TimestampFilter(filter_type, timestamp_type))


class FilterPredicate(Generic[_T]):
    def __init__(self):
        self._owner_name_dict: dict[type[FilterBuilder], str] = {}

    def __set_name__(self, owner: type[FilterBuilder], name: str):
        self._owner_name_dict[owner] = name

    @overload
    def __get__(self, instance: None, owner: type[FilterBuilder]) -> Self:
        pass

    @overload
    def __get__(self, instance: FilterBuilder, owner: type[FilterBuilder]) -> Callable[..., Filter]:
        pass

    @abstractmethod
    def __get__(self, instance: Optional[FilterBuilder], owner: type[FilterBuilder]) -> Callable[..., Filter] | Self:
        pass


class NullaryFilterPredicate(FilterPredicate[_T]):
    def __init__(self, value: _T):
        super().__init__()
        self.value = value

    @overload
    def __get__(self, instance: None, owner: type[FilterBuilder]) -> Self:
        pass

    @overload
    def __get__(self, instance: FilterBuilder, owner: type[FilterBuilder]) -> Callable[[], Filter]:
        pass

    def __get__(self, instance: Optional[FilterBuilder], owner: type[FilterBuilder]) -> Callable[[], Filter] | Self:
        if instance is None:
            return self
        name = self._owner_name_dict[owner]
        return lambda: instance.init_filter(FilterType({name: self.value}))


class UnaryFilterPredicate(FilterPredicate[_T]):
    @overload
    def __get__(self, instance: None, owner: type[FilterBuilder]) -> Self:
        pass

    @overload
    def __get__(self, instance: FilterBuilder, owner: type[FilterBuilder]) -> Callable[[_T], Filter]:
        pass

    def __get__(self, instance: Optional[FilterBuilder], owner: type[FilterBuilder]) -> Callable[[_T], Filter] | Self:
        if instance is None:
            return self
        name = self._owner_name_dict[owner]
        return lambda value: instance.init_filter(FilterType({name: value}))


class TextFilterBuilder(FilterBuilder):
    """eligible property types: ["title", "rich_text", "url", "email", and "phone_number"]"""
    equals = UnaryFilterPredicate[str]()
    does_not_equal = UnaryFilterPredicate[str]()
    contains = UnaryFilterPredicate[str]()
    does_not_contain = UnaryFilterPredicate[str]()
    starts_with = UnaryFilterPredicate[str]()
    ends_with = UnaryFilterPredicate[str]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class NumberFilterBuilder(FilterBuilder):
    """eligible property types: ['number]"""
    equals = UnaryFilterPredicate[int | Decimal]()
    does_not_equal = UnaryFilterPredicate[int | Decimal]()
    greater_than = UnaryFilterPredicate[int | Decimal]()
    less_than = UnaryFilterPredicate[int | Decimal]()
    greater_than_or_equal_to = UnaryFilterPredicate[int | Decimal]()
    less_than_or_equal_to = UnaryFilterPredicate[int | Decimal]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class CheckboxFilterBuilder(FilterBuilder):
    """eligible property types: ['checkbox']"""
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class SelectFilterBuilder(FilterBuilder):
    """eligible property types: ['select', 'status']"""
    equals = UnaryFilterPredicate[str]()
    does_not_equal = UnaryFilterPredicate[str]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class MultiSelectFilterBuilder(FilterBuilder):
    """eligible property types: ['multi_select']"""
    contains = UnaryFilterPredicate[str]()
    does_not_contain = UnaryFilterPredicate[str]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class DateFilterBuilder(FilterBuilder):
    """eligible property types: ["date", "created_time", "last_edited_time"]"""
    equals = UnaryFilterPredicate[datetime]()
    before = UnaryFilterPredicate[datetime]()
    after = UnaryFilterPredicate[datetime]()
    on_or_before = UnaryFilterPredicate[datetime]()
    on_or_after = UnaryFilterPredicate[datetime]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)
    past_week = NullaryFilterPredicate({})
    past_month = NullaryFilterPredicate({})
    past_year = NullaryFilterPredicate({})
    next_week = NullaryFilterPredicate({})
    next_month = NullaryFilterPredicate({})
    next_year = NullaryFilterPredicate({})


class PeopleFilterBuilder(FilterBuilder):
    """eligible property types: ["people", "created_by", and "last_edited_by"]"""
    contains = UnaryFilterPredicate[str]()
    does_not_contain = UnaryFilterPredicate[str]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class FilesFilterBuilder(FilterBuilder):
    """eligible property types: ['files']"""
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)


class RelationFilterBuilder(FilterBuilder):
    """eligible property types: ['relation']"""
    contains = UnaryFilterPredicate[UUID]()
    does_not_contain = UnaryFilterPredicate[UUID]()
    is_empty = NullaryFilterPredicate(True)
    is_not_empty = NullaryFilterPredicate(True)
