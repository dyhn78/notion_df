from db_handler.query_handler__filter_base import QueryFilter
from db_handler.query_handler__filter_maker import QueryFilterMaker, PlainFilter
from db_handler.query_handler__sort import QuerySort as Sort
from db_handler.parser import DatabaseParser as DBParser


class QueryHandler:
    def __init__(self, page_id: str, database_parser=None):
        # retrieve_reader 치우기.
        self.page_id = page_id
        self.page_size = 100
        self.sort = Sort()
        self.filter_handler = QueryFilterHandler()
        self.filter_maker = QueryFilterMaker()
        # self.start_cursor = ''
        if database_parser is not None:
            self.add_db_retrieve(database_parser)

    def add_db_retrieve(self, database_parser: DBParser):
        self.filter_maker.add_db_retrieve(database_parser)

    @property
    def apply(self):
        return {
            'database_id': self.page_id,
            'filter': self.filter_handler.apply,
            'sorts': self.sort.apply,
            # 'start_cursor': self.start_cursor,
            'page_size': self.page_size
        }


class QueryFilterHandler:
    def __init__(self):
        self.apply = PlainFilter({})

    def clear(self):
        self.apply = PlainFilter({})

    def push(self, query_filter: QueryFilter):
        self.apply = query_filter.apply


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