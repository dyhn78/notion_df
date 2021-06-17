from abc import ABC
from pprint import pprint

from db_reader import DatabaseRetrieveReader as DBRetrieveReader


class QueryFilter:
    # TODO: AssertionError 대신 커스텀 에러클래스 정의
    def __init__(self, filter_value: dict, nesting: int, bracket_type: str):
        """nesting 기준이 Notion 앱에서보다 더 강하다.
        예를 들어 any('contains', ['1', 'A', '@'] 형식으로 필터를 구성할 경우
        Notion 앱에서는 nesting == 0이지만, API 상에서는 1로 판정한다."""
        self.apply = filter_value
        self.nesting = nesting
        self.bracket_type = bracket_type
        if self.nesting > 2:
            print('Nested greater than 2!')
            pprint(self.apply)
            raise AssertionError

    def __and__(self, other):
        """filter1 & filter2 형식으로 사용할 수 있다."""
        if self.bracket_type == other.bracket_type and self.bracket_type != 'None':
            return self.__join(other)
        else:
            return DatabaseQueryFilterFrameMaker.all(self, other)

    def __or__(self, other):
        """filter1 | filter2 형식으로 사용할 수 있다."""
        if self.bracket_type == other.bracket_type and self.bracket_type != 'None':
            return self.__join(other)
        else:
            return DatabaseQueryFilterFrameMaker.any(self, other)

    def __join(self, other):
        args = []
        print(args)
        for instance in self, other:
            args.extend(instance.apply[instance.bracket_type])
            print(args)
        filter_value = {self.bracket_type: args}
        return QueryFilter(filter_value, self.nesting, self.bracket_type)


class PropertyFilterFrame(ABC):
    prop_class = None

    def __init__(self, prop_name):
        self.prop_name = prop_name
        assert self.prop_class is not None

    def _build(self, filter_name, arg):
        return QueryFilter({
            'property': self.prop_name,
            self.prop_class: {filter_name: arg}
        }, 0, 'None')

    def is_empty(self):
        return self._build('is_empty', True)

    def is_not_empty(self):
        return self._build('is_not_empty', True)

    def all(self, filter_name, args: list):
        filters = self.__split_list_of_expected_values(filter_name, args)
        return DatabaseQueryFilterFrameMaker.all(*filters)

    def any(self, filter_name, args: list):
        filters = self.__split_list_of_expected_values(filter_name, args)
        return DatabaseQueryFilterFrameMaker.any(*filters)

    def __split_list_of_expected_values(self, filter_name, args):
        filters = []
        for arg in args:
            filters.append(self._build(filter_name, arg))
        return filters


class DatabaseQueryFilterFrameMaker:
    def __init__(self, retrieve_reader: DBRetrieveReader):
        """특정한 데이터베이스 하나를 위한 query_filter 프레임을 만든다."""
        self.database_frame = retrieve_reader.database_frame

    @classmethod
    def all(cls, *filters: QueryFilter):
        nesting = cls.__eval_compound_nest(*filters)
        and_filter = QueryFilter({'and': [ft.apply for ft in filters]}, nesting, 'and')
        return and_filter

    @classmethod
    def any(cls, *filters: QueryFilter):
        nesting = cls.__eval_compound_nest(*filters)
        or_filter = QueryFilter({'or': [ft.apply for ft in filters]}, nesting, 'or')
        return or_filter

    @staticmethod
    def __eval_compound_nest(*filters: QueryFilter):
        return 1 + max(ft.nesting for ft in filters)

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
        return _TextFilter(name)

    @staticmethod
    def number(name: str):
        return _NumberFilter(name)

    @staticmethod
    def checkbox(name: str):
        return _CheckboxFilter(name)

    @staticmethod
    def select(name: str):
        return _SelectFilter(name)

    @staticmethod
    def files(name: str):
        return _FilesFilter(name)

    @staticmethod
    def multi_select(name: str):
        return _MultiselectFilter(name)

    @staticmethod
    def date(name: str):
        return _DateFilter(name)

    @staticmethod
    def people(name: str):
        return _PeopleFilter(name)

    @staticmethod
    def relation(name: str):
        return _RelationFilter(name)


class _TextFilter(PropertyFilterFrame):
    prop_class = 'text'

    def equals(self, arg):
        return self._build('equals', arg)

    def does_not_equal(self, arg):
        return self._build('does_not_equal', arg)

    def contains(self, arg):
        return self._build('contains', str(arg))

    def does_not_contain(self, arg):
        return self._build('does_not_contain', str(arg))

    def starts_with(self, arg):
        return self._build('starts_with', str(arg))

    def ends_with(self, arg):
        return self._build('ends_with', str(arg))


class _NumberFilter(PropertyFilterFrame):
    prop_class = 'number'

    def equals(self, arg):
        return self._build('equals', arg)

    def does_not_equal(self, arg):
        return self._build('does_not_equal', arg)

    def greater_than(self, arg):
        return self._build('greater_than', arg)

    def less_than(self, arg):
        return self._build('less_than', arg)

    def greater_than_or_equal_to(self, arg):
        return self._build('greater_than_or_equal_to', arg)

    def less_than_or_equal_to(self, arg):
        return self._build('less_than_or_equal_to', arg)


class _CheckboxFilter(PropertyFilterFrame):
    prop_class = 'checkbox'

    def equals(self, arg):
        return self._build('equals', arg)

    def does_not_equal(self, arg):
        return self._build('does_not_equal', arg)

    def is_empty(self):
        return self.equals(False)

    def is_not_empty(self):
        return self.equals(True)


class _SelectFilter(PropertyFilterFrame):
    prop_class = 'select'

    def equals(self, arg):
        return self._build('equals', arg)

    def does_not_equal(self, arg):
        return self._build('does_not_equal', arg)


class _MultiselectFilter(PropertyFilterFrame):
    prop_class = 'multi_select'

    def equals(self, arg):
        return self._build('equals', arg)

    def does_not_equal(self, arg):
        return self._build('does_not_equal', arg)

    def contains(self, arg):
        return self._build('contains', arg)

    def does_not_contain(self, arg):
        return self._build('does_not_contain', arg)


class _DateFilter(PropertyFilterFrame):
    prop_class = 'date'

    def equals(self, arg):
        return self._build('equals', arg)

    def before(self, arg):
        return self._build('before', arg)

    def after(self, arg):
        return self._build('after', arg)

    def on_or_before(self, arg):
        return self._build('on_or_before', arg)

    def on_or_after(self, arg):
        return self._build('on_or_after', arg)

    def past_week(self, arg):
        return self._build('past_week', arg)

    def past_month(self, arg):
        return self._build('past_month', arg)

    def past_year(self, arg):
        return self._build('past_year', arg)

    def next_week(self, arg):
        return self._build('next_week', arg)

    def next_month(self, arg):
        return self._build('next_month', arg)

    def next_year(self, arg):
        return self._build('next_year', arg)


class _PeopleFilter(PropertyFilterFrame):
    prop_class = 'people'

    def equals(self, arg):
        return self._build('equals', arg)

    def does_not_equal(self, arg):
        return self._build('does_not_equal', arg)


class _FilesFilter(PropertyFilterFrame):
    prop_class = 'files'


class _RelationFilter(PropertyFilterFrame):
    prop_class = 'relation'

    def contains(self, arg):
        return self._build('contains', arg)

    def does_not_contain(self, arg):
        return self._build('does_not_contain', arg)
