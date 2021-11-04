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

    def attach_page(self, page):
        from .page_row import PageRow
        assert isinstance(page, PageRow)
        self.blocks.append(page)

    def detach_page(self, page):
        from .page_row import PageRow
        assert isinstance(page, PageRow)
        self.blocks.remove(page)
        page.payload.unregister_all()
        del page

    def apply_query_response(self, response):
        parser = PageListParser(response)
        pages = self.apply_pagelist_parser(parser)
        return pages

    def apply_pagelist_parser(self, parser: PageListParser):
        pages = []
        for page_parser in parser:
            pages.append(self.apply_page_parser(page_parser))
        return pages

    def apply_page_parser(self, parser: PageParser):
        page_id = parser.page_id
        if not (page := self.caller.by_id.get(page_id)):
            page = self.caller.open_page(page_id)
        page.props.apply_page_parser(parser)
        return page


class PageListCreator(ListEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.caller = caller
        self.frame = self.caller.frame

        from .page_row import PageRow
        self._values: list[PageRow] = []

    @property
    def blocks(self):
        return self._values

    def attach_page(self, page):
        self.blocks.append(page)
        assert id(page) == id(self.blocks[-1])
        return page

    def detach_page(self, page):
        pass

    def save(self):
        for child in self.blocks:
            child.save()
        res = self.blocks.copy()
        self.blocks.clear()
        return res
