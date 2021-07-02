from db_handler.abstract_structures import Requestor
from db_handler.query__filter_base import QueryFilter
from db_handler.query__filter_handler import QueryFilterMaker, PlainFilter
from db_handler.query__sort_base import QuerySort
from db_handler.parser import DatabaseParser as DBParser


class QueryHandler(Requestor):
    def __init__(self, notion, page_id: str, database_parser=None, start_cursor=None):
        super().__init__(notion)
        self.page_id = page_id
        self.page_size = 100
        self.start_cursor = start_cursor
        self.filter_handler = PlainFilter({})
        self.filter_maker = QueryFilterMaker()
        self.sort_handler = []
        if database_parser is not None:
            self.__add_db_retrieve(database_parser)

    @property
    def apply(self):
        res = {
            'database_id': self.page_id,
            'filter': self.filter_handler.apply,
            'sorts': self.sort_handler,
            'page_size': self.page_size
        }
        if self.start_cursor:
            res['start_cursor'] = self.start_cursor
        return res

    def execute(self):
        return self.notion.databases.query(**self.apply)

    def __add_db_retrieve(self, database_parser: DBParser):
        self.filter_maker.add_db_retrieve(database_parser)

    def clear_filter(self):
        self.filter_handler = PlainFilter({})

    def push_filter(self, query_filter: QueryFilter):
        self.filter_handler = query_filter

    def clear_sort(self):
        self.sort_handler = []

    def append_sort_ascending(self, prop_name):
        self.sort_handler.append(QuerySort.make_ascending_sort(prop_name))

    def append_sort_descending(self, prop_name):
        self.sort_handler.append(QuerySort.make_descending_sort(prop_name))

    def appendleft_sort_ascending(self, prop_name):
        self.sort_handler.insert(0, QuerySort.make_ascending_sort(prop_name))

    def appendleft_sort_descending(self, prop_name):
        self.sort_handler.insert(0, QuerySort.make_descending_sort(prop_name))


"""
default_filter = {'database_id': TEST_DATABASE_ID,
                  'filter': {
                      'or': [{
                          'property': '이름',
                          'text': {'contains': '1'}
                      },
                          {
                              'property': '이름',
                              'text': {'contains': '2'}
                          }]
                  }}
"""