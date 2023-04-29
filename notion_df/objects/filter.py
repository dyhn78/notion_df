from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypeVar, Generic, Optional, Callable, overload, NewType

from typing_extensions import Self

from notion_df.objects.constant import TimestampType
from notion_df.objects.core import Serializable, serialize
from notion_df.objects.misc import UUID

_T = TypeVar('_T')
FilterType = NewType('FilterType', dict)


@dataclass
class Filter(Serializable, metaclass=ABCMeta):
    type_object: dict


@dataclass
class CompoundFilter(Filter):
    operator: Literal['and', 'or']
    elements: list[Filter]

    def serialize(self):
        return {self.operator: serialize(self.elements)}


@dataclass
class PropertyFilter(Filter):
    # https://developers.notion.com/reference/post-database-query-filter
    property_name: str
    property_type: str

    def serialize(self):
        return {
            "property": self.property_name,
            self.property_type: serialize(self.type_object)
        }


@dataclass
class ArrayRollupFilter(PropertyFilter):
    aggregate_type: Literal['any', 'every', 'none']

    def serialize(self):
        return {
            "property": self.property_name,
            "rollup": {
                self.aggregate_type: {
                    self.property_type: serialize(self.type_object)
                }
            }
        }

    def serialize_2(self):
        # TODO: find which is correct by actual testing
        return {
            "property": self.property_name,
            self.aggregate_type: {
                self.property_type: serialize(self.type_object)
            }
        }


@dataclass
class TimestampFilter(Filter):
    timestamp: TimestampType

    def serialize(self):
        return {
            "timestamp_type": self.timestamp,
            self.timestamp: serialize(self.type_object)
        }


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


class FilterBuilder(metaclass=ABCMeta):
    def __init__(self, init_filter: Callable[[FilterType], Filter]):
        self.init_filter = init_filter
        # TODO - implement from caller's side
        #  - init_filter = lambda type_object: PropertyFilter(type_object, property_name, property_type)
        #  - init_filter = lambda type_object: ArrayRollupFilter(type_object, property_name, property_type, aggregate_type)
        #  - init_filter = lambda type_object: TimestampFilter(type_object, timestamp_type)


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
