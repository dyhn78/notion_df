from db_reader.query_handler__filter import QueryFilter, PlainFilter, QueryFilterMaker
from db_reader.query_handler__sort import QuerySort as Sort
from db_reader.parser import DatabaseRetrieveReader as DBRetrieveReader


class QueryHandler:
    def __init__(self, retrieve_reader: DBRetrieveReader):
        # retrieve_reader 치우기.
        self.page_size = 100
        # self.start_cursor = ''
        self.sort = Sort()
        self.filter_handler = QueryFilterHandler()
        self.filter_maker = QueryFilterMaker(retrieve_reader)

    @property
    def apply(self):
        return {
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