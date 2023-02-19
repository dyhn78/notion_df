from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import ClassVar, Literal, TypeVar, Generic, Optional, Callable, final, overload

from typing_extensions import Self

from notion_df.resource.core import Serializable
from notion_df.resource.misc import UUID, Timestamp

_T = TypeVar('_T')
AggregateType = Literal['any', 'every', 'none']


# TODO
#  - implement following 'reduce-like' properties on model-side (i.e. entity and fields).
#    - rollup: number, date
#    - formula: string, checkbox, number, date


@dataclass
class Filter(Serializable, metaclass=ABCMeta):
    clause: dict


@dataclass
class PropertyFilter(Filter):
    # https://developers.notion.com/reference/post-database-query-filter
    property_name: str
    property_type: str

    def plain_serialize(self):
        return {
            "property": self.property_name,
            self.property_type: self.clause
        }


@dataclass
class ArrayRollupFilter(PropertyFilter):
    aggregate_type: AggregateType

    def plain_serialize(self):
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

    def plain_serialize(self):
        return {
            "timestamp": self.timestamp,
            self.timestamp: self.clause
        }


@dataclass
class CompoundFilter(Filter):
    operator: Literal['and', 'or']
    elements: list[Filter]

    def plain_serialize(self):
        return {self.operator: self.elements}


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

    def __get__(self, instance: Optional[FilterBuilder], owner: type[FilterBuilder]) -> Callable[..., Filter] | Self:
        if instance is None:
            return self
        name = self._owner_name_dict[owner]
        return lambda: instance.init_filter({name: self.value})


class UnaryPredicate(Predicate[_T]):
    def __get__(self, instance: Optional[FilterBuilder], owner: type[FilterBuilder]) -> Callable[..., Filter] | Self:
        if instance is None:
            return self
        name = self._owner_name_dict[owner]
        return lambda value: instance.init_filter({name: value})


class FilterBuilder(metaclass=ABCMeta):
    @property
    @final
    def init_filter(self) -> Callable[[dict], Filter]:
        # TODO
        if ...:
            timestamp = ...  # from instance
            return lambda clause: TimestampFilter(clause, timestamp)
        elif ...:
            property_name = property_type = aggregate_type = ...  # from instance
            return lambda clause: ArrayRollupFilter(clause, property_name, property_type, aggregate_type)
        else:
            property_name = property_type = ...  # from instance
            return lambda clause: PropertyFilter(clause, property_name, property_type)


@dataclass
class PropertyFilterBuilder(FilterBuilder):
    property_type: ClassVar[str]


@dataclass
class TextFilterBuilder(PropertyFilterBuilder, metaclass=ABCMeta):
    """available property types: "title", "rich_text", "url", "email", and "phone_number\""""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    starts_with = UnaryPredicate[str]()
    ends_with = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class NumberFilterBuilder(PropertyFilterBuilder):
    """available property types: 'number'"""
    equals = UnaryPredicate[int | Decimal]()
    does_not_equal = UnaryPredicate[int | Decimal]()
    greater_than = UnaryPredicate[int | Decimal]()
    less_than = UnaryPredicate[int | Decimal]()
    greater_than_or_equal_to = UnaryPredicate[int | Decimal]()
    less_than_or_equal_to = UnaryPredicate[int | Decimal]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class CheckboxFilterBuilder(PropertyFilterBuilder):
    """available property types: 'checkbox'"""
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class SelectFilterBuilder(PropertyFilterBuilder):
    """available property types: 'select'"""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class MultiSelectFilterBuilder(PropertyFilterBuilder):
    """available property types: 'multi_select'"""
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class StatusFilterBuilder(PropertyFilterBuilder):
    """available property types: 'status'"""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class DateFilterBuilder(PropertyFilterBuilder):
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


@dataclass
class PeopleFilterBuilder(PropertyFilterBuilder):
    """available property types: "people", "created_by", and "last_edited_by\""""
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class FilesFilterBuilder(PropertyFilterBuilder):
    """available property types: 'files'"""
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)


@dataclass
class RelationFilterBuilder(PropertyFilterBuilder):
    """available property types: 'relation'"""
    contains = UnaryPredicate[UUID]()
    does_not_contain = UnaryPredicate[UUID]()
    is_empty = NullaryPredicate(True)
    is_not_empty = NullaryPredicate(True)
