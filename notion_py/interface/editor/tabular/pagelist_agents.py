from notion_py.interface.parser import PageListParser, PageParser
from .pagelist import PageList
from ..common.struct.agents import ListEditor


class PageListUpdater(ListEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame

        from .page_row import PageRow
        self._values: list[PageRow] = []

    @property
    def blocks(self):
        return self._values

    def apply_pagelist_parser(self, parser: PageListParser):
        pages = []
        for page_parser in parser:
            pages.append(self.apply_page_parser(page_parser))
        return pages

    def apply_page_parser(self, parser: PageParser):
        page_id = parser.page_id
        if not (page := self.caller.by_id.get(page_id)):
            page = self.open_page(page_id)
        page.props.apply_page_parser(parser)
        return page

    def open_page(self, page_id: str):
        from .page_row import PageRow
        page = PageRow(caller=self, page_id=page_id, frame=self.frame)
        self.blocks.append(page)
        return page

    def close_page(self, page):
        from .page_row import PageRow
        assert isinstance(page, PageRow)
        # this will de-register the page from the pagelist.
        page.title = ''
        page.master_id = ''
        self.blocks.remove(page)


class PageListCreator(ListEditor):
    def __init__(self, caller: PageList):
        from .page_row import PageRow
        super().__init__(caller)
        self.caller = caller
        self.frame = self.caller.frame
        self._values: list[PageRow] = []

    @property
    def blocks(self):
        return self._values

    def create_page_row(self):
        from .page_row import PageRow
        page = PageRow.create_new(self)
        self.blocks.append(page)
        assert id(page) == id(self.blocks[-1])
        return page

    def save(self):
        for child in self.blocks:
            child.save()
        res = self.blocks.copy()
        self.blocks.clear()
        return res
