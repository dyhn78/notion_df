from __future__ import annotations
from collections import defaultdict
from pprint import pprint

from .page import TabularPageBlock
from ..abs_supported.master import SupportedBlock
from ...api_parse import PageListParser
from ...gateway import Query
from ...struct import PointEditor, BridgeEditor, PropertyFrame, MasterEditor


class PageList(PointEditor):
    def __init__(self, caller: MasterEditor):
        super().__init__(caller)
        self.caller = caller
        self.frame: PropertyFrame = getattr(caller, 'frame', PropertyFrame())
        self._normal = PageListUpdater(self)
        self._new = PageListCreator(self)
        self.query = Query(self)

    def __bool__(self):
        any([self._normal, self._new])

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, page_id: str):
        return self.by_id[page_id]

    @property
    def elements(self) -> list[TabularPageBlock]:
        return self._normal.values + self._new.values

    @property
    def descendants(self) -> list[SupportedBlock]:
        res = []
        res.extend(self.elements)
        for page in self.elements:
            res.extend(page.sphere.descendants)
        return res

    def keys(self):
        return self.by_id.keys()

    def set_overwrite_option(self, option: bool):
        for child in self.elements:
            child.set_overwrite_option(option)

    @property
    def by_id(self) -> dict[str, TabularPageBlock]:
        return self._normal.by_id

    @property
    def by_title(self) -> dict[str, TabularPageBlock]:
        return {**self._normal.by_title, **self._new.by_title}

    def by_idx_value_of(self, prop_key: str) -> dict[str, TabularPageBlock]:
        try:
            return {page.props.read_of(prop_key): page
                    for page in self.elements}
        except TypeError:
            page_object = self.elements[0]
            pprint(f"key : {page_object.props.read_of(prop_key)}")
            pprint(f"value : {page_object.master_id}")
            raise TypeError

    def by_idx_value_at(self, prop_tag: str):
        return self.by_idx_value_of(self.frame.key_at(prop_tag))

    def by_value_of(self, prop_key: str) -> dict[str, list[TabularPageBlock]]:
        res = defaultdict(list)
        for page in self.elements:
            res[page.props.read_of(prop_key)].append(page)
        return res

    def by_value_at(self, prop_tag: str):
        return self.by_value_of(self.frame.key_at(prop_tag))

    def new_tabular_page(self):
        return self._new.new_tabular_page()

    def run_query(self, page_size=0):
        response = self.query.execute(page_size=page_size)
        parser = PageListParser(response)
        self._normal.apply_parser(parser)
        self.query = Query(self)

    def make_preview(self):
        return {'pages': self._normal.make_preview(),
                'new_pages': self._new.make_preview()}

    def execute(self):
        self._normal.execute()
        response = self._new.execute()
        self._normal.values.extend(response)


class PageListUpdater(BridgeEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.values: list[TabularPageBlock] = []
        self.frame = caller.frame
        self.by_id = {}
        self.by_title: dict[str, TabularPageBlock] = {}

    def apply_parser(self, parser: PageListParser):
        for page_parser in parser:
            page = TabularPageBlock(caller=self, page_id=page_parser.page_id)
            page.props.apply_page_parser(page_parser)
            self.values.append(page)
            self.by_id[page.master_id] = page
            self.by_title[page.title] = page


class PageListCreator(BridgeEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.caller = caller
        self.values: list[TabularPageBlock] = []

    @property
    def by_title(self) -> dict[str, TabularPageBlock]:
        return {page.title: page for page in self.values}

    def new_tabular_page(self):
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
