from __future__ import annotations
from .filter_unit import PlainFilter, OrFilter, AndFilter
from ...struct import Gateway, PropertyFrame, PropertyUnit

# find types by api_format
FILTER_TYPES = {
    'text': ['text', 'title', 'rich_text', 'url', 'email', 'phone_number'],
    'date': ['date', 'created_time', 'last_edited_time'],
    'people': ['people', 'person', 'created_by', 'last_edited_by']
}
# find api_format by type
FILTER_FORMATS = {}
for form, types in FILTER_TYPES.items():
    FILTER_FORMATS.update(**{typ: form for typ in types})


class QueryFilterAgent:
    def __init__(self, caller: Gateway):
        """특정한 데이터베이스 하나를 위한 query_filter 프레임을 만든다."""
        self.caller = caller
        self.frame = self.caller.frame if hasattr(self.caller, 'frame') \
            else PropertyFrame()

    def of(self, prop_name: str, prop_type=None) -> FilterMaker:
        if prop_type == 'formula':
            format_type = prop_type
            assert prop_type in ['text', 'checkbox', 'number', 'date']
        elif prop_type == 'rollup':
            format_type = prop_type
        else:
            if prop_type is None:
                prop_type = self.frame.type_of(prop_name)
            format_type = FILTER_FORMATS[prop_type]
        frame_func = f'{format_type}_of'
        return getattr(self, frame_func)(prop_name)

    def at(self, prop_key: str, prop_type=None):
        return self.of(self.frame.name_at(prop_key), prop_type)

    def text_of(self, prop_name: str):
        return TextFilterMaker(self, prop_name)

    def relation_of(self, prop_name: str):
        return RelationFilterMaker(self, prop_name)

    def number_of(self, prop_name: str):
        return NumberFilterMaker(self, prop_name)

    def checkbox_of(self, prop_name: str):
        return CheckboxFilterMaker(self, prop_name)

    def select_of(self, prop_name: str):
        return SelectFilterMaker(self, prop_name)

    def multi_select_of(self, prop_name: str):
        return MultiselectFilterMaker(self, prop_name)

    def files_of(self, prop_name: str):
        return FilesFilterMaker(self, prop_name)

    def date_of(self, prop_name: str):
        return DateFilterMaker(self, prop_name)

    def people_of(self, prop_name: str):
        return PeopleFilterMaker(self, prop_name)

    def text_at(self, prop_key: str):
        return self.text_of(self.frame.name_at(prop_key))

    def relation_at(self, prop_key: str):
        return self.relation_of(self.frame.name_at(prop_key))

    def number_at(self, prop_key: str):
        return self.number_of(self.frame.name_at(prop_key))

    def checkbox_at(self, prop_key: str):
        return self.checkbox_of(self.frame.name_at(prop_key))

    def select_at(self, prop_key: str):
        return self.select_of(self.frame.name_at(prop_key))

    def multi_select_at(self, prop_key: str):
        return self.multi_select_of(self.frame.name_at(prop_key))

    def files_at(self, prop_key: str):
        return self.files_of(self.frame.name_at(prop_key))

    def date_at(self, prop_key: str):
        return self.date_of(self.frame.name_at(prop_key))

    def people_at(self, prop_key: str):
        return self.people_of(self.frame.name_at(prop_key))


class FilterMaker:
    prop_type = None

    def __init__(self, caller: QueryFilterAgent, prop_name):
        assert self.prop_type is not None
        self.prop_name: str = prop_name
        self.frame_unit: PropertyUnit = \
            caller.frame.by_name[prop_name] if prop_name in caller.frame.by_name \
            else PropertyUnit(prop_name)
        self.values = self.frame_unit.values
        self.value_groups = self.frame_unit.value_groups

    def _wrap_as_filter(self, filter_type, arg):
        return PlainFilter({
            'property': self.prop_name,
            self.prop_type: {filter_type: arg}
        })

    def is_empty(self):
        return self._wrap_as_filter('is_empty', True)

    def is_not_empty(self):
        return self._wrap_as_filter('is_not_empty', True)


class EqualtypeFilterMaker(FilterMaker):
    def equals(self, value):
        return self._wrap_as_filter('equals', value)

    def does_not_equal(self, value):
        return self._wrap_as_filter('does_not_equal', value)

    def equals_to_any(self, values):
        return OrFilter([self.equals(value) for value in values])

    def equals_to_none(self, values):
        return AndFilter([self.does_not_equal(value) for value in values])


class ContaintypeFilterMaker(FilterMaker):
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


class FilesFilterMaker(FilterMaker):
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

    def does_not_equal(self, value):
        return OrFilter([self.before(value), self.after(value)])

    def before(self, value: str):
        return self._wrap_as_filter('before', value)

    def after(self, value: str):
        return self._wrap_as_filter('after', value)

    def on_or_before(self, value: str):
        return self._wrap_as_filter('on_or_before', value)

    def on_or_after(self, value: str):
        return self._wrap_as_filter('on_or_after', value)

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
