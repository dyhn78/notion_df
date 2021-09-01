from .filter_maker import QueryFilterMaker
from .filter_unit import QueryFilter, PlainFilter
from .sort import QuerySort
from notion_py.interface.struct import LongGateway, retry_request


class Query(LongGateway):
    def __init__(self, database_id: str, name='', database_parser=None):
        super().__init__(name)
        self.database_id = database_id
        self.filter = PlainFilter({})
        self.sort = QuerySort()
        self.filter_maker = QueryFilterMaker()
        if database_parser is not None:
            self.filter_maker.add_db_retrieve(database_parser)

    def __bool__(self):
        return True

    def unpack(self, page_size=None, start_cursor=None):
        args = dict(**self.sort.unpack(),
                    database_id=self.database_id,
                    page_size=page_size if page_size else self.MAX_PAGE_SIZE)
        if self.filter:
            args.update(filter=self.filter.unpack())
        if start_cursor:
            args.update(start_cursor=start_cursor)
        return args

    @retry_request
    def _execute_once(self, page_size=None, start_cursor=None):
        response = self.notion.databases.query(
            **self.unpack(page_size=page_size, start_cursor=start_cursor)
        )
        return response

    def clear_filter(self):
        self.filter = PlainFilter({})

    def push_filter(self, query_filter: QueryFilter):
        self.filter = query_filter
