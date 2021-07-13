# from pprint import pprint

from .filter_maker import QueryFilterMaker
from .filter_unit import QueryFilter, PlainFilter
from .sort import QuerySort
from notion_py.interface.structure import RecursiveRequestor, retry


class Query(RecursiveRequestor):
    def __init__(self, page_id: str, database_parser=None):
        self.page_id = page_id
        self._id_apply = {'database_id': page_id}
        self._filter = PlainFilter({})
        self._filter_is_not_empty = False
        self.sort = QuerySort()
        self.filter_maker = QueryFilterMaker()
        if database_parser is not None:
            self.filter_maker.add_db_retrieve(database_parser)

    def apply(self, print_result=False):
        filter_apply = {'filter': self._filter.apply()} \
            if self._filter_is_not_empty else None
        return self._merge_dict(self._id_apply, self.sort.apply(), filter_apply)

    @retry
    def _execute_once(self, page_size=None, start_cursor=None):
        page_size = {'page_size': (page_size if page_size else self.MAX_PAGE_SIZE)}
        start_cursor = {'start_cursor': start_cursor} if start_cursor else None
        args = self._merge_dict(self.apply(), start_cursor, page_size)
        response = self.notion.databases.query(**args)
        return response

    def clear_filter(self):
        self._filter = PlainFilter({})
        self._filter_is_not_empty = False

    def push_filter(self, query_filter: QueryFilter):
        self._filter = query_filter
        self._filter_is_not_empty = True
