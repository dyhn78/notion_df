from interface.requests.structures import Requestor
from query_filter_unit import QueryFilter, PlainFilter
from query_filter_frame import QueryFilterMaker
from query_sort import QuerySort


class DatabaseQuery(Requestor):
    def __init__(self, notion, page_id: str, page_size=100, database_parser=None, start_cursor=None):
        super().__init__(notion)
        self.page_id = {'database_id': page_id}
        self.page_size = {'page_size': page_size}
        self.start_cursor = {'start_cursor': start_cursor} if start_cursor else None
        self.filter = PlainFilter({})
        self.filter_maker = QueryFilterMaker()
        self.sort = QuerySort()
        if database_parser is not None:
            self.filter_maker.add_db_retrieve(database_parser)

    def apply(self):
        return self.merge_dict(
            self.page_id,
            self.page_size,
            self.start_cursor,
            self.sort.apply(),
            {'filter': self.filter.apply()}
        )

    def execute(self):
        return self.notion.databases.query(**self.apply())

    def clear_filter(self):
        self.filter = PlainFilter({})

    def push_filter(self, query_filter: QueryFilter):
        self.filter = query_filter
