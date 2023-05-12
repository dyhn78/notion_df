from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime, date
from typing import Literal, Any, Callable, Optional
from uuid import UUID

from notion_df.object.constant import TimestampName, Number
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
    typename: str
    condition: FilterCondition

    def serialize(self):
        return {
            "property": self.name_or_id,
            self.typename: serialize(self.condition)
        }


@dataclass
class FormulaPropertyFilter(Filter):
    name_or_id: str | UUID
    typename: str
    value_typename: str
    condition: FilterCondition

    def serialize(self):
        return {
            "property": self.name_or_id,
            self.typename: {self.value_typename: serialize(self.condition)}
        }


@dataclass
class RollupPropertyAggregateFilter(Filter):
    name_or_id: str | UUID
    aggregate_type: RollupAggregate
    typename: str
    condition: FilterCondition

    def serialize(self):
        return {
            "property": self.name_or_id,
            "rollup": {
                self.aggregate_type: {
                    self.typename: serialize(self.condition)
                }
            }
        }

    def serialize2(self):
        # TODO: find which is correct by actual testing
        return {
            "property": self.name_or_id,
            self.aggregate_type: {
                self.typename: serialize(self.condition)
            }
        }


@dataclass
class TimestampFilter(Filter):
    name: TimestampName
    condition: FilterCondition

    def serialize(self):
        return {
            "timestamp_type": self.name,
            self.name: serialize(self.condition)
        }


@dataclass
class FilterBuilder(metaclass=ABCMeta):
    def __init__(self, build: Callable[[FilterCondition], Filter]):
        self._build = build

    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass


class TextFilterBuilder(FilterBuilder):
    """eligible property types: ["title", "rich_text", "url", "email", and "phone_number"]"""

    @classmethod
    def get_typename(cls) -> str:
        return 'text'

    def equals(self, value: str) -> Filter:
        return self._build({'equals': value})

    def does_not_equal(self, value: str) -> Filter:
        return self._build({'does_not_equal': value})

    def contains(self, value: str) -> Filter:
        return self._build({'contains': value})

    def does_not_contain(self, value: str) -> Filter:
        return self._build({'does_not_contain': value})

    def starts_with(self, value: str) -> Filter:
        return self._build({'starts_with': value})

    def ends_with(self, value: str) -> Filter:
        return self._build({'ends_with': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})


class NumberFilterBuilder(FilterBuilder):
    """eligible property types: ['number']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'number'

    def equals(self, value: Number) -> Filter:
        return self._build({'equals': value})

    def does_not_equal(self, value: Number) -> Filter:
        return self._build({'does_not_equal': value})

    def greater_than(self, value: Number) -> Filter:
        return self._build({'greater_than': value})

    def less_than(self, value: Number) -> Filter:
        return self._build({'less_than': value})

    def greater_than_or_equal_to(self, value: Number) -> Filter:
        return self._build({'greater_than_or_equal_to': value})

    def less_than_or_equal_to(self, value: Number) -> Filter:
        return self._build({'less_than_or_equal_to': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})


class CheckboxFilterBuilder(FilterBuilder):
    """eligible property types: ['checkbox']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'checkbox'

    def equals(self, value: bool) -> Filter:
        return self._build({'equals': value})

    def does_not_equal(self, value: bool) -> Filter:
        return self._build({'does_not_equal': value})

    def is_empty(self) -> Filter:
        return self.equals(False)

    def is_not_empty(self) -> Filter:
        return self.equals(True)


class SelectFilterBuilder(FilterBuilder):
    """eligible property types: ['select', 'status']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'select'

    def equals(self, value: Optional[str]) -> Filter:
        if value is None:
            return self.is_empty()
        return self._build({'equals': value})

    def does_not_equal(self, value: Optional[str]) -> Filter:
        if value is None:
            return self.is_not_empty()
        return self._build({'does_not_equal': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})


class MultiSelectFilterBuilder(FilterBuilder):
    """eligible property types: ['multi_select']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'multi_select'

    def contains(self, value: str) -> Filter:
        return self._build({'contains': value})

    def does_not_contain(self, value: str) -> Filter:
        return self._build({'does_not_contain': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})


class DateFilterBuilder(FilterBuilder):
    """eligible property types: ["date", "created_time", "last_edited_time"]"""

    @classmethod
    def get_typename(cls) -> str:
        return 'date'

    def equals(self, value: date | datetime) -> Filter:
        return self._build({'equals': value})

    def before(self, value: date | datetime) -> Filter:
        return self._build({'before': value})

    def after(self, value: date | datetime) -> Filter:
        return self._build({'after': value})

    def on_or_before(self, value: date | datetime) -> Filter:
        return self._build({'on_or_before': value})

    def on_or_after(self, value: date | datetime) -> Filter:
        return self._build({'on_or_after': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})

    def past_week(self) -> Filter:
        return self._build({'past_week': {}})

    def past_month(self) -> Filter:
        return self._build({'past_month': {}})

    def past_year(self) -> Filter:
        return self._build({'past_year': {}})

    def next_week(self) -> Filter:
        return self._build({'next_week': {}})

    def next_month(self) -> Filter:
        return self._build({'next_month': {}})

    def next_year(self) -> Filter:
        return self._build({'next_year': {}})


class PeopleFilterBuilder(FilterBuilder):
    """eligible property types: ["people", "created_by", and "last_edited_by"]"""

    @classmethod
    def get_typename(cls) -> str:
        return 'people'

    def contains(self, value: str) -> Filter:
        return self._build({'contains': value})

    def does_not_contain(self, value: str) -> Filter:
        return self._build({'does_not_contain': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})


class FilesFilterBuilder(FilterBuilder):
    """eligible property types: ['files']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'files'

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})


class RelationFilterBuilder(FilterBuilder):
    """eligible property types: ['relation']"""

    @classmethod
    def get_typename(cls) -> str:
        return 'relation'

    def contains(self, value: UUID) -> Filter:
        return self._build({'contains': value})

    def does_not_contain(self, value: UUID) -> Filter:
        return self._build({'does_not_contain': value})

    def is_empty(self) -> Filter:
        return self._build({'is_empty': True})

    def is_not_empty(self) -> Filter:
        return self._build({'is_not_empty': True})
