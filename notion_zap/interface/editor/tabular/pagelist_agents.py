from .pagelist import PageList
from ..struct import ListEditor
from notion_zap.interface.gateway import parsers


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
