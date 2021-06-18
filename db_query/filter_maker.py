from abc import ABC, abstractmethod
from pprint import pprint

from db_reader import DatabaseRetrieveReader as DBRetrieveReader


class QueryFilter(ABC):
    """참고로, nesting 기준이 Notion 앱에서보다 더 강하다.
    예를 들어 any('contains', ['1', 'A', '@'] 형식으로 필터를 구성할 경우
    Notion 앱에서는 nesting == 0이지만, API 상에서는 1로 판정한다."""
    @property
    @abstractmethod
    def apply(self):
        pass

    @property
    @abstractmethod
    def nesting(self):
        pass

    def __and__(self, other):
        """filter1 & filter2 형식으로 사용할 수 있다."""
        return AndFilter(self, other)

    def __or__(self, other):
        """filter1 | filter2 형식으로 사용할 수 있다."""
        return OrFilter(self, other)


class CompoundFilter(QueryFilter):
    def __init__(self, *elements):
        homos = []
        heteros = []
        for e in elements:
            if type(e) == type(self):
                homos.append(e)
            else:
                heteros.append(e)

        self._nesting = 0
        if homos:
            self._nesting = max(e.nesting for e in homos)
        if heteros:
            self._nesting = max(self._nesting, 1 + max(e.nesting for e in heteros))
        if self.nesting > 2:
            # TODO: AssertionError 대신 커스텀 에러클래스 정의
            print('Nested greater than 2!')
            pprint(self.apply)
            raise AssertionError

        self.elements = heteros
        for e in homos:
            self.elements.extend(e.elements)

    @property
    @abstractmethod
    def apply(self):
        pass

    @property
    def nesting(self):
        return self._nesting


class AndFilter(CompoundFilter):
    @property
    def apply(self):
        return {'and': list(e.apply for e in self.elements)}


class OrFilter(CompoundFilter):
    @property
    def apply(self):
        return {'or': list(e.apply for e in self.elements)}


class QueryFilterFrameMaker:
    def __init__(self, retrieve_reader: DBRetrieveReader):
        """특정한 데이터베이스 하나를 위한 query_filter 프레임을 만든다."""
        self.database_frame = retrieve_reader.database_frame

    def __call__(self, name: str, value_type=None):
        """알맞은 PropertyFilters를 자동으로 찾아 반환한다."""
        prop_class = self.__get_prop_class(name, value_type)
        return getattr(self, prop_class)(name)

    def __get_prop_class(self, name, value_type):
        if name == 'formula':
            prop_class = value_type
            assert value_type in ['text', 'checkbox', 'number', 'date']
        elif name == 'rollup':
            prop_class = value_type
        else:
            prop_type = self.database_frame[name]
            if prop_type in ['title', 'rich_text', 'url', 'email', 'phone_number']:
                prop_class = 'text'
            elif prop_type in ['created_time', 'last_edited_time']:
                prop_class = 'date'
            elif prop_type in ['created_by', 'last_edited_by']:
                prop_class = 'people'
            else:
                prop_class = prop_type
        return prop_class

    @staticmethod
    def text(name: str):
        return TextFrame(name)

    @staticmethod
    def number(name: str):
        return NumberFrame(name)

    @staticmethod
    def checkbox(name: str):
        return CheckboxFrame(name)

    @staticmethod
    def select(name: str):
        return SelectFrame(name)

    @staticmethod
    def files(name: str):
        return FilesFrame(name)

    @staticmethod
    def multi_select(name: str):
        return MultiselectFrame(name)

    @staticmethod
    def date(name: str):
        return DateFrame(name)

    @staticmethod
    def people(name: str):
        return PeopleFrame(name)

    @staticmethod
    def relation(name: str):
        return RelationFrame(name)


class PlainQueryFilter(QueryFilter):
    def __init__(self, plain_filter_value: dict):
        self._apply = plain_filter_value

    @property
    def apply(self):
        return self._apply

    @property
    def nesting(self):
        return 0


class PlainFilterFrame:
    prop_class = None

    def __init__(self, prop_name):
        self.prop_name = prop_name
        assert self.prop_class is not None

    def make_filter(self, filter_type, arg):
        return PlainQueryFilter({
            'property': self.prop_name,
            self.prop_class: {filter_type: arg}
        })

    def is_empty(self):
        return self.make_filter('is_empty', True)

    def is_not_empty(self):
        return self.make_filter('is_not_empty', True)


class EqualtypeFrame(ABC, PlainFilterFrame):
    def equals(self, arg):
        return self.make_filter('equals', arg)

    def does_not_equal(self, arg):
        return self.make_filter('does_not_equal', arg)

    def equals_to_any(self, *args):
        return OrFilter(self.equals(arg) for arg in args)

    def equals_to_none(self, *args):
        return AndFilter(self.does_not_equal(arg) for arg in args)


class ContaintypeFrame(ABC, PlainFilterFrame):
    def contains(self, arg):
        return self.make_filter('contains', str(arg))

    def does_not_contain(self, arg):
        return self.make_filter('does_not_contain', str(arg))

    def contains_any(self, *args):
        return OrFilter(self.contains(arg) for arg in args)

    def contains_all(self, *args):
        return AndFilter(self.contains(arg) for arg in args)

    def contains_none(self, *args):
        return AndFilter(self.does_not_contain(arg) for arg in args)

    def contains_not_all(self, *args):
        return OrFilter(self.does_not_contain(arg) for arg in args)


class TextFrame(EqualtypeFrame, ContaintypeFrame):
    prop_class = 'text'

    def starts_with(self, arg):
        return self.make_filter('starts_with', str(arg))

    def ends_with(self, arg):
        return self.make_filter('ends_with', str(arg))

    def starts_with_one_of(self, *args):
        return OrFilter(self.starts_with(arg) for arg in args)

    def ends_with_one_of(self, *args):
        return AndFilter(self.ends_with(arg) for arg in args)


class NumberFrame(EqualtypeFrame):
    prop_class = 'number'

    def greater_than(self, arg):
        return self.make_filter('greater_than', arg)

    def less_than(self, arg):
        return self.make_filter('less_than', arg)

    def greater_than_or_equal_to(self, arg):
        return self.make_filter('greater_than_or_equal_to', arg)

    def less_than_or_equal_to(self, arg):
        return self.make_filter('less_than_or_equal_to', arg)


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

    def does_not_equal(self, arg):
        return OrFilter(self.before(arg), self.after(arg))

    def before(self, arg):
        return self.make_filter('before', arg)

    def after(self, arg):
        return self.make_filter('after', arg)

    def on_or_before(self, arg):
        return self.make_filter('on_or_before', arg)

    def on_or_after(self, arg):
        return self.make_filter('on_or_after', arg)

    def past_week(self, arg):
        return self.make_filter('past_week', arg)

    def past_month(self, arg):
        return self.make_filter('past_month', arg)

    def past_year(self, arg):
        return self.make_filter('past_year', arg)

    def next_week(self, arg):
        return self.make_filter('next_week', arg)

    def next_month(self, arg):
        return self.make_filter('next_month', arg)

    def next_year(self, arg):
        return self.make_filter('next_year', arg)


class PeopleFrame(EqualtypeFrame, ContaintypeFrame):
    prop_class = 'people'


class FilesFrame(PlainFilterFrame):
    prop_class = 'files'


class RelationFrame(ContaintypeFrame):
    prop_class = 'relation'
