from ..struct import ListEditor
from .pagelist import PageList
from notion_py.interface.parser import PageListParser


class PageListUpdater(ListEditor):
    def __init__(self, caller: PageList):
        from .page import TabularPageBlock
        super().__init__(caller)
        self.caller = caller
        self.values: list[TabularPageBlock] = []
        self.frame = caller.frame
        self.by_id: dict[str, TabularPageBlock] = {}
        self.by_title: dict[str, TabularPageBlock] = {}

    def apply_parser(self, parser: PageListParser):
        from .page import TabularPageBlock
        for page_parser in parser:
            page = TabularPageBlock(caller=self, page_id=page_parser.page_id)
            page.props.apply_page_parser(page_parser)
            self.values.append(page)
            self.by_id[page.master_id] = page
            self.by_title[page.title] = page


class PageListCreator(ListEditor):
    def __init__(self, caller: PageList):
        from .page import TabularPageBlock
        super().__init__(caller)
        self.caller = caller
        self.values: list[TabularPageBlock] = []

    @property
    def by_title(self):
        res = {}
        for page in self.values:
            res[page.title] = page
        return res

    def create_tabular_page(self):
        from .page import TabularPageBlock
        page = TabularPageBlock.create_new(self)
        self.values.append(page)
        assert id(page) == id(self.values[-1])
        return page

    def execute(self):
        for child in self:
            # individual tabular_page will update themselves.
            child.fetch_children()
        res = self.values.copy()
        self.values.clear()
        return res
