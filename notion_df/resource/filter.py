from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar, ParamSpec, Literal, TypeVar, Generic

from notion_df.resource.core import Serializable
from notion_df.resource.misc import UUID, Timestamp

_P = ParamSpec('_P')
AggregateOption = Literal['any', 'every', 'none']

# TODO
#  - implement following 'reduce-like' properties on model-side (i.e. entity and fields).
#    - rollup: number, date
#    - formula: string, checkbox, number, date


_T = TypeVar('_T')


class Predicate(Generic[_T]):
    name: str

    def __set_name__(self, owner, name: str):
        # TODO: allow reusing one descriptor for multiple filter_builders
        assert not getattr(self, 'owner')
        self.owner = owner
        self.name = name

    @abstractmethod
    def __call__(self, **kwargs) -> dict[str, _T]:
        pass


class UnaryPredicate(Predicate[_T]):
    def __call__(self, value: _T) -> dict[str, _T]:
        return {self.name: value}


class FixedPredicate(Predicate[_T]):
    def __init__(self, value: _T):
        self.value = value

    def __call__(self) -> dict[str, _T]:
        return {self.name: self.value}


class EmptyPredicate(Predicate):
    def __call__(self) -> dict:
        return {}


@dataclass
class FilterCondition:
    type: str
    inner_value: Any

    def property(self, property_name: str, property_type: str):
        return PropertyFilter(self, property_name, property_type)

    def rollup(self, option: AggregateOption, property_name: str, property_type: str):
        return ArrayRollupPropertyFilter(self, property_name, property_type, option)


@dataclass
class DateFilterCondition(FilterCondition):
    def timestamp(self, option: Timestamp):
        return TimestampFilter(self, option)


@dataclass
class Filter(Serializable, metaclass=ABCMeta):
    pass


@dataclass
class PropertyFilter(Filter):
    # https://developers.notion.com/reference/post-database-query-filter
    condition: FilterCondition
    property: str
    property_type: str

    def plain_serialize(self):
        return {
            "property": self.property,
            self.property_type: self.condition
        }


@dataclass
class ArrayRollupPropertyFilter(PropertyFilter):
    aggregate: AggregateOption

    def plain_serialize(self):
        return {
            "property": self.property,
            "rollup": {
                self.aggregate: {
                    self.property_type: self.condition
                }
            }
        }

    def plain_serialize_2(self):
        # TODO: find which is correct by actual testing
        return {
            "property": self.property,
            self.aggregate: {
                self.property_type: self.condition
            }
        }


@dataclass
class TimestampFilter(Filter):
    condition: FilterCondition
    timestamp: Timestamp

    def plain_serialize(self):
        return {
            "timestamp": self.timestamp,
            self.timestamp: self.condition
        }


@dataclass
class CompoundFilter(Filter):
    operator: Literal['and', 'or']
    elements: list[Filter]

    def plain_serialize(self):
        return {self.operator: self.elements}


class FilterBuilder(metaclass=ABCMeta):
    pass


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
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class NumberFilterBuilder(PropertyFilterBuilder):
    """available property types: 'number'"""
    equals = UnaryPredicate[int | Decimal]()
    does_not_equal = UnaryPredicate[int | Decimal]()
    greater_than = UnaryPredicate[int | Decimal]()
    less_than = UnaryPredicate[int | Decimal]()
    greater_than_or_equal_to = UnaryPredicate[int | Decimal]()
    less_than_or_equal_to = UnaryPredicate[int | Decimal]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class CheckboxFilterBuilder(PropertyFilterBuilder):
    """available property types: 'checkbox'"""
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class SelectFilterBuilder(PropertyFilterBuilder):
    """available property types: 'select'"""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class MultiSelectFilterBuilder(PropertyFilterBuilder):
    """available property types: 'multi_select'"""
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class StatusFilterBuilder(PropertyFilterBuilder):
    """available property types: 'status'"""
    equals = UnaryPredicate[str]()
    does_not_equal = UnaryPredicate[str]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class DateFilterBuilder(PropertyFilterBuilder):
    """available property types: "date", "created_time", and "last_edited_time\""""
    equals = UnaryPredicate[datetime]()
    before = UnaryPredicate[datetime]()
    after = UnaryPredicate[datetime]()
    on_or_before = UnaryPredicate[datetime]()
    on_or_after = UnaryPredicate[datetime]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)
    past_week = EmptyPredicate()
    past_month = EmptyPredicate()
    past_year = EmptyPredicate()
    next_week = EmptyPredicate()
    next_month = EmptyPredicate()
    next_year = EmptyPredicate()


@dataclass
class PeopleFilterBuilder(PropertyFilterBuilder):
    """available property types: "people", "created_by", and "last_edited_by\""""
    contains = UnaryPredicate[str]()
    does_not_contain = UnaryPredicate[str]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class FilesFilterBuilder(PropertyFilterBuilder):
    """available property types: 'files'"""
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)


@dataclass
class RelationFilterBuilder(PropertyFilterBuilder):
    """available property types: 'relation'"""
    contains = UnaryPredicate[UUID]()
    does_not_contain = UnaryPredicate[UUID]()
    is_empty = FixedPredicate(True)
    is_not_empty = FixedPredicate(True)
