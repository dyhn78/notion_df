from typing import Any

from notion_zap.cli.core.save_agents import ListEditor
from notion_zap.cli.gateway import parsers
from .database import RowChildren
from ..row.main import PageRow
from ...core import PropertyFrame


class RowChildrenUpdater(ListEditor):
    def __init__(self, caller: RowChildren):
        self.frame = caller.frame if caller.frame else PropertyFrame()
        ListEditor.__init__(self, caller)
        self.caller = caller
        self._values = []

    @property
    def values(self) -> list[PageRow]:
        return self._values

    def attach_page(self, page):
        assert isinstance(page, PageRow)
        self.values.append(page)

    def detach_page(self, page):
        assert isinstance(page, PageRow)
        self.values.remove(page)

    def apply_query_response(self, response):
        parser = parsers.PageListParser(response)
        pages = self.apply_pagelist_parser(parser)
        return pages

    def apply_pagelist_parser(self, parser: parsers.PageListParser):
        pages = []
        for page_parser in parser:
            page = self.apply_page_parser(page_parser)
            if page is not None:
                pages.append(page)
        return pages

    def apply_page_parser(self, parser: parsers.PageParser):
        page_id = parser.page_id
        if page_id in self.caller.ids():
            page = self.caller.by_id[page_id]
        else:
            if self.root.exclude_archived and parser.archived:
                return None
            page = self.caller.open_page(page_id)
        page.apply_page_parser(parser)
        return page

    def read(self) -> dict[str, Any]:
        return {'children': [child.read() for child in self.values]}

    def richly_read(self) -> dict[str, Any]:
        return {'children': [child.richly_read() for child in self.values]}


class RowChildrenCreator(ListEditor):
    def __init__(self, caller: RowChildren):
        self.frame = caller.frame if caller.frame else PropertyFrame()
        ListEditor.__init__(self, caller)
        self.caller = caller

        self._values = []

    @property
    def values(self) -> list[PageRow]:
        return self._values

    def attach_page(self, page):
        self.values.append(page)
        assert id(page) == id(self.values[-1])
        return page

    def detach_page(self, page):
        pass

    def save(self):
        for child in self.values:
            child.save()
        res = self.values.copy()
        self.values.clear()
        return res

    def read(self) -> dict[str, Any]:
        return {'new_children': [child.read() for child in self.values]}

    def richly_read(self) -> dict[str, Any]:
        return {'new_children': [child.richly_read() for child in self.values]}
