from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Literal, TypeVar, Generic, Optional, Callable, overload

from typing_extensions import Self

from notion_df.resource.core import Serializable
from notion_df.resource.misc import UUID, Timestamp

_T = TypeVar('_T')


@dataclass
class Filter(Serializable, metaclass=ABCMeta):
    clause: dict


@dataclass
class CompoundFilter(Filter):
    operator: Literal['and', 'or']
    elements: list[Filter]

    def _plain_serialize(self):
        return {self.operator: self.elements}


@dataclass
class PropertyFilter(Filter):
    # https://developers.notion.com/reference/post-database-query-filter
    property_name: str
    property_type: str

    def _plain_serialize(self):
        return {
            "property": self.property_name,
            self.property_type: self.clause
        }


@dataclass
class ArrayRollupFilter(PropertyFilter):
    aggregate_type: Literal['any', 'every', 'none']

    def _plain_serialize(self):
        return {
            "property": self.property_name,
            "rollup": {
                self.aggregate_type: {
                    self.property_type: self.clause
                }
            }
        }

    def plain_serialize_2(self):
        # TODO: find which is correct by actual testing
        return {
            "property": self.property_name,
            self.aggregate_type: {
                self.property_type: self.clause
            }
        }


@dataclass
class TimestampFilter(Filter):
    timestamp: Timestamp

    def _plain_serialize(self):
        return {
            "timestamp": self.timestamp,
            self.timestamp: self.clause
        }


class Predicate(Generic[_T]):
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


class NullaryPredicate(Predicate[_T]):
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
        return lambda: instance.init_filter({name: self.value})


class UnaryPredicate(Predicate[_T]):
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
        return lambda value: instance.init_filter({name: value})


class FilterBuilder(metaclass=ABCMeta):
    def __init__(self, init_filter: Callable[[dict], Filter]):
        self.init_filter = init_filter
        # TODO - implement from caller's side
        #  -  init_filter = lambda clause: PropertyFilter(clause, property_name, property_type)
        #  -  init_filter = lambda clause: ArrayRollupFilter(clause, property_name, property_type, aggregate_type)
        #  -  init_filter = lambda clause: TimestampFilter(clause, timestamp)


class TextFilterBuilder(FilterBuilder, metaclass=ABCMeta):
    """available property types: "title", "rich_text", "url", "email", and "phone_number\""""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    starts_with = UnaryPredicate[str]()
    ends_with = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class NumberFilterBuilder(FilterBuilder):
    """available property types: 'number'"""
    equals = UnaryPredicate[int | Decimal]()
    does_not_equal = UnaryPredicate[int | Decimal]()
    greater_than = UnaryPredicate[int | Decimal]()
    less_than = UnaryPredicate[int | Decimal]()
    greater_than_or_equal_to = UnaryPredicate[int | Decimal]()
    less_than_or_equal_to = UnaryPredicate[int | Decimal]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class CheckboxFilterBuilder(FilterBuilder):
    """available property types: 'checkbox'"""
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class SelectFilterBuilder(FilterBuilder):
    """available property types: 'select'"""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class MultiSelectFilterBuilder(FilterBuilder):
    """available property types: 'multi_select'"""
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class StatusFilterBuilder(FilterBuilder):
    """available property types: 'status'"""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class DateFilterBuilder(FilterBuilder):
    """available property types: "date", "created_time", and "last_edited_time\""""
    equals = UnaryPredicate[datetime]()
    before = UnaryPredicate[datetime]()
    after = UnaryPredicate[datetime]()
    on_or_before = UnaryPredicate[datetime]()
    on_or_after = UnaryPredicate[datetime]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)
    past_week = NullaryPredicate({})
    past_month = NullaryPredicate({})
    past_year = NullaryPredicate({})
    next_week = NullaryPredicate({})
    next_month = NullaryPredicate({})
    next_year = NullaryPredicate({})


class PeopleFilterBuilder(FilterBuilder):
    """available property types: "people", "created_by", and "last_edited_by\""""
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class FilesFilterBuilder(FilterBuilder):
    """available property types: 'files'"""
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


class RelationFilterBuilder(FilterBuilder):
    """available property types: 'relation'"""
    contains = UnaryPredicate[UUID]()
    does_not_contain = UnaryPredicate[UUID]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)
