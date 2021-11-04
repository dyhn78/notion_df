from typing import Callable

from notion_py.interface.editor.common.struct import BlockEditor
from .filter_unit import QueryFilter, EmptyFilter
from ..struct import LongRequestor, print_response_error
from ...common import PropertyFrame
from ...utility import page_id_to_url, stopwatch


class Query(LongRequestor):
    def __init__(self, editor: BlockEditor, frame: PropertyFrame):
        super().__init__(editor)
        self.frame = frame
        self._filter_value = EmptyFilter()

        from .filter_maker import QueryFilterMaker
        self.filter_maker = QueryFilterMaker(self)

        from .sort import QuerySort
        self.sort = QuerySort()

    def __bool__(self):
        return True

    @staticmethod
    def open_filter():
        return EmptyFilter()

    def push_filter(self, ft: QueryFilter):
        self._filter_value = ft

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
        return response
        # from ...editor.tabular.pagelist_agents import PageListUpdater
        # assert isinstance(self.editor, PageListUpdater)
        # pages = self.editor.apply_query_response(response)
        # return pages

    @print_response_error
    def _execute_each(self, request_size, start_cursor=None):
        response = self.notion.databases.query(
            **self.encode(request_size, start_cursor)
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


class QueryWithCallback(Query):
    def __init__(self, editor: BlockEditor, frame: PropertyFrame,
                 execute_callback: Callable):
        super().__init__(editor, frame)
        self.callback = execute_callback

    def execute(self, request_size=0):
        response = super().execute(request_size)
        self.callback(response)
