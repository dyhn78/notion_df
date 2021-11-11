from __future__ import annotations
from typing import Union
from datetime import datetime as datetimeclass, date as dateclass

from notion_zap.cli.struct import PropertyColumn
from .filter_unit import PlainFilter, OrFilter, AndFilter
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


class QueryFilterMaker:
    def __init__(self, query: Query):
        """특정한 데이터베이스 하나를 위한 query_filter 프레임을 만든다."""
        self.query = query
        self.frame = self.query.frame

    def of(self, prop_key: str, prop_type=None) -> QueryFilterAgent:
        if prop_type == 'formula':
            format_type = prop_type
            assert prop_type in ['text', 'checkbox', 'number', 'date']
        elif prop_type == 'rollup':
            format_type = prop_type
        else:
            if prop_type is None:
                prop_type = self.frame.type_of(prop_key)
            format_type = FILTER_FORMATS[prop_type]
        frame_func = f'{format_type}_of'
        return getattr(self, frame_func)(prop_key)

    def at(self, prop_tag: str, prop_type=None):
        return self.of(self.frame.key_at(prop_tag), prop_type)

    def text_of(self, prop_key: str):
        return TextFilterAgent(self, prop_key)

    def relation_of(self, prop_key: str):
        return RelationFilterAgent(self, prop_key)

    def number_of(self, prop_key: str):
        return NumberFilterAgent(self, prop_key)

    def checkbox_of(self, prop_key: str):
        return CheckboxFilterAgent(self, prop_key)

    def select_of(self, prop_key: str):
        return SelectFilterAgent(self, prop_key)

    def multi_select_of(self, prop_key: str):
        return MultiselectFilterAgent(self, prop_key)

    def files_of(self, prop_key: str):
        return FilesFilterAgent(self, prop_key)

    def date_of(self, prop_key: str):
        return DateFilterAgent(self, prop_key)

    def people_of(self, prop_key: str):
        return PeopleFilterAgent(self, prop_key)

    def text_at(self, prop_tag: str):
        return self.text_of(self.frame.key_at(prop_tag))

    def relation_at(self, prop_tag: str):
        return self.relation_of(self.frame.key_at(prop_tag))

    def number_at(self, prop_tag: str):
        return self.number_of(self.frame.key_at(prop_tag))

    def checkbox_at(self, prop_tag: str):
        return self.checkbox_of(self.frame.key_at(prop_tag))

    def select_at(self, prop_tag: str):
        return self.select_of(self.frame.key_at(prop_tag))

    def multi_select_at(self, prop_tag: str):
        return self.multi_select_of(self.frame.key_at(prop_tag))

    def files_at(self, prop_tag: str):
        return self.files_of(self.frame.key_at(prop_tag))

    def date_at(self, prop_tag: str):
        return self.date_of(self.frame.key_at(prop_tag))

    def people_at(self, prop_tag: str):
        return self.people_of(self.frame.key_at(prop_tag))


class QueryFilterAgent:
    prop_type = None

    def __init__(self, filter_maker: QueryFilterMaker, prop_key):
        assert self.prop_type is not None
        self.prop_key: str = prop_key
        self.frame_cl: PropertyColumn = (
            filter_maker.frame.by_key[prop_key]
            if prop_key in filter_maker.frame.by_key
            else PropertyColumn(prop_key)
        )
        self.prop_values = self.frame_cl.prop_values
        self.prop_value_groups = self.frame_cl.prop_value_groups

    def _wrap_as_filter(self, filter_type, arg):
        return PlainFilter({
            'property': self.prop_key,
            self.prop_type: {filter_type: arg}
        })

    def is_empty(self):
        return self._wrap_as_filter('is_empty', True)

    def is_not_empty(self):
        return self._wrap_as_filter('is_not_empty', True)


class EqualtypeFilterAgent(QueryFilterAgent):
    def equals(self, value):
        return self._wrap_as_filter('equals', value)

    def does_not_equal(self, value):
        return self._wrap_as_filter('does_not_equal', value)

    def equals_to_any(self, values):
        return OrFilter([self.equals(value) for value in values])

    def equals_to_none(self, values):
        return AndFilter([self.does_not_equal(value) for value in values])


class ContaintypeFilterAgent(QueryFilterAgent):
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


class SelectFilterAgent(EqualtypeFilterAgent):
    prop_type = 'select'


class MultiselectFilterAgent(EqualtypeFilterAgent, ContaintypeFilterAgent):
    prop_type = 'multi_select'


class PeopleFilterAgent(EqualtypeFilterAgent, ContaintypeFilterAgent):
    prop_type = 'people'


class FilesFilterAgent(QueryFilterAgent):
    prop_type = 'files'


class RelationFilterAgent(ContaintypeFilterAgent):
    prop_type = 'relation'


class TextFilterAgent(EqualtypeFilterAgent, ContaintypeFilterAgent):
    prop_type = 'text'

    def starts_with(self, value):
        return self._wrap_as_filter('starts_with', str(value))

    def ends_with(self, value):
        return self._wrap_as_filter('ends_with', str(value))

    def starts_with_one_of(self, values):
        return OrFilter([self.starts_with(value) for value in values])

    def ends_with_one_of(self, values):
        return AndFilter([self.ends_with(value) for value in values])


class NumberFilterAgent(EqualtypeFilterAgent):
    prop_type = 'number'

    def greater_than(self, value):
        return self._wrap_as_filter('greater_than', value)

    def less_than(self, value):
        return self._wrap_as_filter('less_than', value)

    def greater_than_or_equal_to(self, value):
        return self._wrap_as_filter('greater_than_or_equal_to', value)

    def less_than_or_equal_to(self, value):
        return self._wrap_as_filter('less_than_or_equal_to', value)


class CheckboxFilterAgent(EqualtypeFilterAgent):
    prop_type = 'checkbox'

    def is_empty(self):
        return self.equals(False)

    def is_not_empty(self):
        return self.equals(True)


class DateFilterAgent(EqualtypeFilterAgent):
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
