from .filter_unit import PlainFilter, OrFilter, AndFilter
from ..parse_deprecated import DatabaseParser


class QueryFilterMaker:
    # TODO : ValueCarrier 클래스를 상속하도록 고치기
    #  (우선순위는 높지 않은 편. 일단 돌아가는 데는 문제가 없으니)
    def __init__(self):
        """특정한 데이터베이스 하나를 위한 query_filter 프레임을 만든다."""
        self.__types_table = None

    def __call__(self, prop_name: str, value_type=None):
        """알맞은 PropertyFilters를 자동으로 찾아 반환한다."""
        if self.__types_table is None:
            raise AssertionError
        prop_class = self.__get_prop_class(prop_name, value_type)
        return getattr(self, prop_class)(prop_name)

    def add_db_retrieve(self, database_parser: DatabaseParser):
        self.__types_table = database_parser.prop_type_table

    def __get_prop_class(self, name, value_type):
        if name == 'formula':
            prop_class = value_type
            assert value_type in ['text', 'checkbox', 'number', 'date']
        elif name == 'rollup':
            prop_class = value_type
        else:
            prop_type = self.__types_table[name]
            if prop_type in ['text', 'title', 'rich_text', 'url', 'email', 'phone_number']:
                prop_class = 'text'
            elif prop_type in ['date', 'created_time', 'last_edited_time']:
                prop_class = 'date'
            elif prop_type in ['people', 'person', 'created_by', 'last_edited_by']:
                prop_class = 'people'
            else:
                prop_class = prop_type
        return prop_class

    @staticmethod
    def by_text(prop_name: str):
        return TextFrame(prop_name)

    @staticmethod
    def by_relation(prop_name: str):
        return RelationFrame(prop_name)

    @staticmethod
    def by_number(prop_name: str):
        return NumberFrame(prop_name)

    @staticmethod
    def by_checkbox(prop_name: str):
        return CheckboxFrame(prop_name)

    @staticmethod
    def by_select(prop_name: str):
        return SelectFrame(prop_name)

    @staticmethod
    def by_multi_select(prop_name: str):
        return MultiselectFrame(prop_name)

    @staticmethod
    def by_files(prop_name: str):
        return FilesFrame(prop_name)

    @staticmethod
    def by_date(prop_name: str):
        return DateFrame(prop_name)

    @staticmethod
    def by_people(prop_name: str):
        return PeopleFrame(prop_name)


class PlainFrame:
    prop_class = None

    def __init__(self, prop_name):
        self.prop_name = prop_name
        assert self.prop_class is not None

    def _wrap_as_filter(self, filter_type, arg):
        return PlainFilter({
            'property': self.prop_name,
            self.prop_class: {filter_type: arg}
        })

    def is_empty(self):
        return self._wrap_as_filter('is_empty', True)

    def is_not_empty(self):
        return self._wrap_as_filter('is_not_empty', True)


class EqualtypeFrame(PlainFrame):
    def equals(self, value):
        return self._wrap_as_filter('equals', value)

    def does_not_equal(self, value):
        return self._wrap_as_filter('does_not_equal', value)

    def equals_to_any(self, *values):
        return OrFilter([self.equals(value) for value in values])

    def equals_to_none(self, *values):
        return AndFilter([self.does_not_equal(value) for value in values])


class ContaintypeFrame(PlainFrame):
    def contains(self, value):
        return self._wrap_as_filter('contains', str(value))

    def does_not_contain(self, value):
        return self._wrap_as_filter('does_not_contain', str(value))

    def contains_any(self, *values):
        return OrFilter([self.contains(value) for value in values])

    def contains_all(self, *values):
        return AndFilter([self.contains(value) for value in values])

    def contains_none(self, *values):
        return AndFilter([self.does_not_contain(value) for value in values])

    def contains_not_all(self, *values):
        return OrFilter([self.does_not_contain(value) for value in values])


class TextFrame(EqualtypeFrame, ContaintypeFrame):
    prop_class = 'text'

    def starts_with(self, value):
        return self._wrap_as_filter('starts_with', str(value))

    def ends_with(self, value):
        return self._wrap_as_filter('ends_with', str(value))

    def starts_with_one_of(self, *values):
        return OrFilter([self.starts_with(value) for value in values])

    def ends_with_one_of(self, *values):
        return AndFilter([self.ends_with(value) for value in values])


class NumberFrame(EqualtypeFrame):
    prop_class = 'number'

    def greater_than(self, value):
        return self._wrap_as_filter('greater_than', value)

    def less_than(self, value):
        return self._wrap_as_filter('less_than', value)

    def greater_than_or_equal_to(self, value):
        return self._wrap_as_filter('greater_than_or_equal_to', value)

    def less_than_or_equal_to(self, value):
        return self._wrap_as_filter('less_than_or_equal_to', value)


class CheckboxFrame(EqualtypeFrame):
    prop_class = 'checkbox'

    def is_empty(self):
        return self.equals(False)

    def is_not_empty(self):
        return self.equals(True)


class SelectFrame(EqualtypeFrame):
    prop_class = 'select'


class MultiselectFrame(EqualtypeFrame, ContaintypeFrame):
    prop_class = 'multi_select'


class DateFrame(EqualtypeFrame):
    prop_class = 'date'

    def does_not_equal(self, value):
        return OrFilter([self.before(value), self.after(value)])

    def before(self, value):
        return self._wrap_as_filter('before', value)

    def after(self, value):
        return self._wrap_as_filter('after', value)

    def on_or_before(self, arg):
        return self._wrap_as_filter('on_or_before', arg)

    def on_or_after(self, arg):
        return self._wrap_as_filter('on_or_after', arg)

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


class PeopleFrame(EqualtypeFrame, ContaintypeFrame):
    prop_class = 'people'


class FilesFrame(PlainFrame):
    prop_class = 'files'


class RelationFrame(ContaintypeFrame):
    prop_class = 'relation'
