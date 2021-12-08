from __future__ import annotations
from typing import Union
from datetime import datetime as datetimeclass, date as dateclass

from notion_zap.cli.structs import PropertyColumn
from .filter_struct import SimpleFilter, OrFilter, AndFilter
from .query import Query

# find config by parsers
FILTER_TYPES = {
    'text': ['text', 'title', 'rich_text', 'url', 'email', 'phone_number'],
    'date': ['date', 'created_time', 'last_edited_time'],
    'people': ['people', 'person', 'created_by', 'last_edited_by']
}
# find parsers by type
FILTER_FORMATS = {}
for form, types in FILTER_TYPES.items():
    FILTER_FORMATS.update(**{typ: form for typ in types})


class QueryFilterManagerbyKey:
    def __init__(self, query: Query):
        self.query = query
        self.frame = self.query.frame

    def __call__(self, prop_key: str, prop_type=None) -> QueryFilterMaker:
        format_type = self._get_attr_name(prop_key, prop_type)
        return getattr(self, format_type)(prop_key)

    def _get_attr_name(self, prop_key, prop_type):
        if prop_type == 'formula':
            format_type = prop_type
            assert prop_type in ['text', 'checkbox', 'number', 'date']
        elif prop_type == 'rollup':
            format_type = prop_type
        else:
            if prop_type is None:
                prop_type = self.frame.type_of(prop_key)
            format_type = FILTER_FORMATS[prop_type]
        return format_type

    def text(self, prop_key: str):
        return TextFilterMaker(self, prop_key)

    def relation(self, prop_key: str):
        return RelationFilterMaker(self, prop_key)

    def number(self, prop_key: str):
        return NumberFilterMaker(self, prop_key)

    def checkbox(self, prop_key: str):
        return CheckboxFilterMaker(self, prop_key)

    def select(self, prop_key: str):
        return SelectFilterMaker(self, prop_key)

    def multi_select(self, prop_key: str):
        return MultiselectFilterMaker(self, prop_key)

    def files(self, prop_key: str):
        return FilesFilterMaker(self, prop_key)

    def date(self, prop_key: str):
        return DateFilterMaker(self, prop_key)

    def people(self, prop_key: str):
        return PeopleFilterMaker(self, prop_key)


class QueryFilterManagerbyTag(QueryFilterManagerbyKey):
    def __call__(self, prop_tag: str, prop_type=None):
        return super().__call__(prop_tag, prop_type)

    def text(self, prop_tag: str):
        return super().text(self.frame.key_of(prop_tag))

    def relation(self, prop_tag: str):
        return super().relation(self.frame.key_of(prop_tag))

    def number(self, prop_tag: str):
        return super().number(self.frame.key_of(prop_tag))

    def checkbox(self, prop_tag: str):
        return super().checkbox(self.frame.key_of(prop_tag))

    def select(self, prop_tag: str):
        return super().select(self.frame.key_of(prop_tag))

    def multi_select(self, prop_tag: str):
        return super().multi_select(self.frame.key_of(prop_tag))

    def files(self, prop_tag: str):
        return super().files(self.frame.key_of(prop_tag))

    def date(self, prop_tag: str):
        return super().date(self.frame.key_of(prop_tag))

    def people(self, prop_tag: str):
        return super().people(self.frame.key_of(prop_tag))


class QueryFilterMaker:
    prop_type = None

    def __init__(self, filter_maker: QueryFilterManagerbyKey, prop_key):
        assert self.prop_type is not None
        self.prop_key: str = prop_key
        self.column: PropertyColumn = (
            filter_maker.frame.by_key[prop_key]
            if prop_key in filter_maker.frame.by_key
            else PropertyColumn(prop_key)
        )

    def _wrap_as_filter(self, filter_type, arg):
        return SimpleFilter({
            'property': self.prop_key,
            self.prop_type: {filter_type: arg}
        })

    def is_empty(self):
        return self._wrap_as_filter('is_empty', True)

    def is_not_empty(self):
        return self._wrap_as_filter('is_not_empty', True)


class EqualtypeFilterMaker(QueryFilterMaker):
    def equals(self, value):
        return self._wrap_as_filter('equals', value)

    def does_not_equal(self, value):
        return self._wrap_as_filter('does_not_equal', value)

    def equals_to_any(self, values):
        return OrFilter([self.equals(value) for value in values])

    def equals_to_none(self, values):
        return AndFilter([self.does_not_equal(value) for value in values])


class ContaintypeFilterMaker(QueryFilterMaker):
    def contains(self, value):
        return self._wrap_as_filter('contains', str(value))

    def does_not_contain(self, value):
        return self._wrap_as_filter('does_not_contain', str(value))

    def contains_any(self, values):
        return OrFilter([self.contains(value) for value in values])

    def contains_all(self, values):
        return AndFilter([self.contains(value) for value in values])

    def contains_none(self, values):
        return AndFilter([self.does_not_contain(value) for value in values])

    def contains_not_all(self, values):
        return OrFilter([self.does_not_contain(value) for value in values])


class SelectFilterMaker(EqualtypeFilterMaker):
    prop_type = 'select'


class MultiselectFilterMaker(EqualtypeFilterMaker, ContaintypeFilterMaker):
    prop_type = 'multi_select'


class PeopleFilterMaker(EqualtypeFilterMaker, ContaintypeFilterMaker):
    prop_type = 'people'


class FilesFilterMaker(QueryFilterMaker):
    prop_type = 'files'


class RelationFilterMaker(ContaintypeFilterMaker):
    prop_type = 'relation'


class TextFilterMaker(EqualtypeFilterMaker, ContaintypeFilterMaker):
    prop_type = 'text'

    def starts_with(self, value):
        return self._wrap_as_filter('starts_with', str(value))

    def ends_with(self, value):
        return self._wrap_as_filter('ends_with', str(value))

    def starts_with_one_of(self, values):
        return OrFilter([self.starts_with(value) for value in values])

    def ends_with_one_of(self, values):
        return AndFilter([self.ends_with(value) for value in values])


class NumberFilterMaker(EqualtypeFilterMaker):
    prop_type = 'number'

    def greater_than(self, value):
        return self._wrap_as_filter('greater_than', value)

    def less_than(self, value):
        return self._wrap_as_filter('less_than', value)

    def greater_than_or_equal_to(self, value):
        return self._wrap_as_filter('greater_than_or_equal_to', value)

    def less_than_or_equal_to(self, value):
        return self._wrap_as_filter('less_than_or_equal_to', value)


class CheckboxFilterMaker(EqualtypeFilterMaker):
    prop_type = 'checkbox'

    def is_empty(self):
        return self.equals(False)

    def is_not_empty(self):
        return self.equals(True)


class DateFilterMaker(EqualtypeFilterMaker):
    prop_type = 'date'

    def does_not_equal(self, value: Union[datetimeclass, dateclass]):
        return OrFilter([self.before(value), self.after(value)])

    def before(self, value: Union[datetimeclass, dateclass]):
        value_str = value.isoformat()
        return self._wrap_as_filter('before', value_str)

    def after(self, value: Union[datetimeclass, dateclass]):
        value_str = value.isoformat()
        return self._wrap_as_filter('after', value_str)

    def on_or_before(self, value: Union[datetimeclass, dateclass]):
        value_str = value.isoformat()
        return self._wrap_as_filter('on_or_before', value_str)

    def on_or_after(self, value: Union[datetimeclass, dateclass]):
        value_str = value.isoformat()
        return self._wrap_as_filter('on_or_after', value_str)

    def within_past_week(self):
        return self._wrap_as_filter('past_week', {})

    def within_past_month(self):
        return self._wrap_as_filter('past_month', {})

    def within_past_year(self):
        return self._wrap_as_filter('past_year', {})

    def within_next_week(self):
        return self._wrap_as_filter('next_week', {})

    def within_next_month(self):
        return self._wrap_as_filter('next_month', {})

    def within_next_year(self):
        return self._wrap_as_filter('next_year', {})
