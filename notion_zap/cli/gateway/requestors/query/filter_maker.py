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

    def __call__(self, key: str, data_type=None) -> QueryFilterMaker:
        format_type = self._get_attr_name(key, data_type)
        return getattr(self, format_type)(key)

    def _get_attr_name(self, key, data_type):
        if data_type == 'formula':
            format_type = data_type
            assert data_type in ['text', 'checkbox', 'number', 'date']
        elif data_type == 'rollup':
            format_type = data_type
        else:
            if data_type is None:
                data_type = self.frame.get_type(key)
            format_type = FILTER_FORMATS[data_type]
        return format_type

    def text(self, key: str):
        return TextFilterMaker(self, key)

    def relation(self, key: str):
        return RelationFilterMaker(self, key)

    def number(self, key: str):
        return NumberFilterMaker(self, key)

    def checkbox(self, key: str):
        return CheckboxFilterMaker(self, key)

    def select(self, key: str):
        return SelectFilterMaker(self, key)

    def multi_select(self, key: str):
        return MultiselectFilterMaker(self, key)

    def files(self, key: str):
        return FilesFilterMaker(self, key)

    def date(self, key: str):
        return DateFilterMaker(self, key)

    def people(self, key: str):
        return PeopleFilterMaker(self, key)


class QueryFilterManagerbyTag(QueryFilterManagerbyKey):
    def __call__(self, key_alias: str, data_type=None):
        return super().__call__(key_alias, data_type)

    def text(self, key_alias: str):
        return super().text(self.frame.get_key(key_alias))

    def relation(self, key_alias: str):
        return super().relation(self.frame.get_key(key_alias))

    def number(self, key_alias: str):
        return super().number(self.frame.get_key(key_alias))

    def checkbox(self, key_alias: str):
        return super().checkbox(self.frame.get_key(key_alias))

    def select(self, key_alias: str):
        return super().select(self.frame.get_key(key_alias))

    def multi_select(self, key_alias: str):
        return super().multi_select(self.frame.get_key(key_alias))

    def files(self, key_alias: str):
        return super().files(self.frame.get_key(key_alias))

    def date(self, key_alias: str):
        return super().date(self.frame.get_key(key_alias))

    def people(self, key_alias: str):
        return super().people(self.frame.get_key(key_alias))


class QueryFilterMaker:
    data_type = None

    def __init__(self, filter_maker: QueryFilterManagerbyKey, key):
        assert self.data_type is not None
        self.key: str = key
        self.column: PropertyColumn = (
            filter_maker.frame.by_key[key]
            if key in filter_maker.frame.by_key
            else PropertyColumn(key)
        )

    def _wrap_as_filter(self, filter_type, arg):
        return SimpleFilter({
            'property': self.key,
            self.data_type: {filter_type: arg}
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
    data_type = 'select'


class MultiselectFilterMaker(EqualtypeFilterMaker, ContaintypeFilterMaker):
    data_type = 'multi_select'


class PeopleFilterMaker(EqualtypeFilterMaker, ContaintypeFilterMaker):
    data_type = 'people'


class FilesFilterMaker(QueryFilterMaker):
    data_type = 'files'


class RelationFilterMaker(ContaintypeFilterMaker):
    data_type = 'relation'


class TextFilterMaker(EqualtypeFilterMaker, ContaintypeFilterMaker):
    data_type = 'text'

    def starts_with(self, value):
        return self._wrap_as_filter('starts_with', str(value))

    def ends_with(self, value):
        return self._wrap_as_filter('ends_with', str(value))

    def starts_with_one_of(self, values):
        return OrFilter([self.starts_with(value) for value in values])

    def ends_with_one_of(self, values):
        return AndFilter([self.ends_with(value) for value in values])


class NumberFilterMaker(EqualtypeFilterMaker):
    data_type = 'number'

    def greater_than(self, value):
        return self._wrap_as_filter('greater_than', value)

    def less_than(self, value):
        return self._wrap_as_filter('less_than', value)

    def greater_than_or_equal_to(self, value):
        return self._wrap_as_filter('greater_than_or_equal_to', value)

    def less_than_or_equal_to(self, value):
        return self._wrap_as_filter('less_than_or_equal_to', value)


class CheckboxFilterMaker(EqualtypeFilterMaker):
    data_type = 'checkbox'

    def is_empty(self):
        return self.equals(False)

    def is_not_empty(self):
        return self.equals(True)


class DateFilterMaker(EqualtypeFilterMaker):
    data_type = 'date'

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
