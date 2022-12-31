import functools
from abc import ABCMeta
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal
from typing import Any, ClassVar, ParamSpec, Literal

from notion_df.resource.core import Resource
from notion_df.resource.misc import UUID, Timestamp

_P = ParamSpec('_P')
AggregateOption = Literal['any', 'every', 'none']


# TODO
#  - implement following 'reduce-like' properties on model-side (i.e. entity and fields).
#    - rollup: number, date
#    - formula: string, checkbox, number, date


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


def condition(func: Callable[_P, ...]) -> Callable[_P, FilterCondition]:
    @functools.wraps(func)
    def wrapper(self: PropertyFilterBuilder, *args: _P.args, **kwargs: _P.kwargs):
        return FilterCondition(func.__name__, func(self, *args, **kwargs))

    return wrapper


def date_condition(func: Callable[_P, ...]) -> Callable[_P, DateFilterCondition]:
    @functools.wraps(func)
    def wrapper(self: PropertyFilterBuilder, *args: _P.args, **kwargs: _P.kwargs):
        return DateFilterCondition(func.__name__, func(self, *args, **kwargs))

    return wrapper


@dataclass
class Filter(Resource, metaclass=ABCMeta):
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
    filters: list[Filter]

    def plain_serialize(self):
        return {self.operator: self.filters}


class FilterBuilder(metaclass=ABCMeta):
    pass


@dataclass
class PropertyFilterBuilder(FilterBuilder):
    property_type: ClassVar[str]


@dataclass
class TextFilterBuilder(PropertyFilterBuilder, metaclass=ABCMeta):
    """available property types: "title", "rich_text", "url", "email", and "phone_number\""""

    @condition
    def equals(self, string: str):
        return string

    @condition
    def does_not_equal(self, string: str):
        return string

    @condition
    def contains(self, string: str):
        return string

    @condition
    def does_not_contain(self, string: str):
        return string

    @condition
    def starts_with(self, string: str):
        return string

    @condition
    def ends_with(self, string: str):
        return string

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class NumberFilterBuilder(PropertyFilterBuilder):
    """available property types: 'number'"""

    @condition
    def equals(self, number: int | Decimal):
        return number

    @condition
    def does_not_equal(self, number: int | Decimal):
        return number

    @condition
    def greater_than(self, number: int | Decimal):
        return number

    @condition
    def less_than(self, number: int | Decimal):
        return number

    @condition
    def greater_than_or_equal_to(self, number: int | Decimal):
        return number

    @condition
    def less_than_or_equal_to(self, number: int | Decimal):
        return number

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class CheckboxFilterBuilder(PropertyFilterBuilder):
    """available property types: 'checkbox'"""

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class SelectFilterBuilder(PropertyFilterBuilder):
    """available property types: 'select'"""

    @condition
    def equals(self, string: str):
        return string

    @condition
    def does_not_equal(self, string: str):
        return string

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class MultiSelectFilterBuilder(PropertyFilterBuilder):
    """available property types: 'multi_select'"""

    @condition
    def contains(self, string: str):
        return string

    @condition
    def does_not_contain(self, string: str):
        return string

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class StatusFilterBuilder(PropertyFilterBuilder):
    """available property types: 'status'"""

    @condition
    def equals(self, string: str):
        return string

    @condition
    def does_not_equal(self, string: str):
        return string

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class DateFilterBuilder(PropertyFilterBuilder):
    """available property types: "date", "created_time", and "last_edited_time\""""

    @date_condition
    def equals(self, dt: datetime):
        return dt

    @date_condition
    def before(self, dt: datetime):
        return dt

    @date_condition
    def after(self, dt: datetime):
        return dt

    @date_condition
    def on_or_before(self, dt: datetime):
        return dt

    @date_condition
    def on_or_after(self, dt: datetime):
        return dt

    @date_condition
    def is_empty(self):
        return True

    @date_condition
    def is_not_empty(self):
        return True

    @date_condition
    def past_week(self):
        return {}

    @date_condition
    def past_month(self):
        return {}

    @date_condition
    def past_year(self):
        return {}

    @date_condition
    def this_week(self):
        return {}

    @date_condition
    def next_week(self):
        return {}

    @date_condition
    def next_month(self):
        return {}

    @date_condition
    def next_year(self):
        return {}


@dataclass
class PeopleFilterBuilder(PropertyFilterBuilder):
    """available property types: "people", "created_by", and "last_edited_by\""""

    @condition
    def contains(self, string: str):
        return string

    @condition
    def does_not_contain(self, string: str):
        return string

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class FilesFilterBuilder(PropertyFilterBuilder):
    """available property types: 'files'"""

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True


@dataclass
class RelationFilterBuilder(PropertyFilterBuilder):
    """available property types: 'relation'"""

    @condition
    def contains(self, string: UUID):
        return string

    @condition
    def does_not_contain(self, string: UUID):
        return string

    @condition
    def is_empty(self):
        return True

    @condition
    def is_not_empty(self):
        return True
