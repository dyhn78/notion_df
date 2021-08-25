from .filter_maker import QueryFilterMaker
from .filter_unit import QueryFilter, PlainFilter
from .sort import QuerySort
from ...common import LongGateway, retry_request


class Query(LongGateway):
    def __init__(self, database_id: str, database_parser=None):
        self.page_id = database_id
        self._filter = PlainFilter({})
        self._filter_is_not_empty = False
        self.sort = QuerySort()
        self.filter_maker = QueryFilterMaker()
        if database_parser is not None:
            self.filter_maker.add_db_retrieve(database_parser)

    def __bool__(self):
        return True

    def unpack(self, print_result=False):
        args = dict(**self.sort.unpack(),
                    database_id=self.page_id)
        if self._filter_is_not_empty:
            args.update(filter=self._filter.unpack())
        return args

    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        args = dict(**self.unpack(),
                    page_size=page_size if page_size else self.MAX_PAGE_SIZE)
        if start_cursor:
            args.update(start_cursor=start_cursor)
        response = self.notion.databases.query(**args)
        return response

    def clear_filter(self):
        self._filter = PlainFilter({})
        self._filter_is_not_empty = False

    def push_filter(self, query_filter: QueryFilter):
        self._filter = query_filter
        self._filter_is_not_empty = True
