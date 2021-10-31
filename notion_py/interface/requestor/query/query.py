from notion_py.interface.editor.common.struct import PointEditor
from .filter_unit import QueryFilter, EmptyFilter
from ..struct import TruthyLongRequestor, print_response_error
from ...common import PropertyFrame
from ...utility import page_id_to_url, stopwatch


class Query(TruthyLongRequestor):
    def __init__(self, editor: PointEditor, frame: PropertyFrame):
        super().__init__(editor)
        self.frame = frame
        self._filter_value = EmptyFilter()

        from .filter_maker import QueryFilterAgent
        self.make_filter = QueryFilterAgent(self)

        from .sort import QuerySort
        self.sort = QuerySort()

    @staticmethod
    def open_filter():
        return EmptyFilter()

    def push_filter(self, query_filter: QueryFilter):
        self._filter_value = query_filter

    def clear_filter(self):
        self._filter_value = EmptyFilter()

    def encode(self, request_size=None, start_cursor=None):
        args = dict(**self.sort.unpack(),
                    database_id=self.target_id,
                    page_size=request_size if request_size else self.MAX_PAGE_SIZE)
        if self._filter_value:
            args.update(filter=self._filter_value.encode())
        if start_cursor:
            args.update(start_cursor=start_cursor)
        return args

    def execute(self, request_size=0):
        self.print_comments()
        response = self._execute_all(request_size, print_comments_each=True)

        from ...editor.tabular.pagelist import PageList
        assert isinstance(self.editor, PageList)
        pages = self.editor.apply_query_response(response)
        return pages

    @print_response_error
    def _execute_each(self, request_size, start_cursor=None):
        response = self.notion.databases.query(
            **self.encode()
        )
        return response

    def print_comments(self):
        target_url = page_id_to_url(self.target_id)
        if self.target_name:
            form = [f"{self.target_name}", target_url]
        else:
            form = ['query', target_url]
        comments = '  '.join(form)
        stopwatch(comments)
