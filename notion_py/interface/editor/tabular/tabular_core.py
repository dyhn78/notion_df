from __future__ import annotations
from collections import defaultdict
from pprint import pprint
from typing import Optional, Union

from .props import TabularProperty
from ..inline.inline_core import ChildBearingBlock
from notion_py.interface.api_parse import PageListParser, DatabaseParser
from ...gateway import RetrieveDatabase, Query
from ...struct import Editor, PointEditor, BridgeEditor, PropertyFrame, MasterEditor


class Database(MasterEditor):
    def __init__(self, caller: Union[PointEditor, Editor],
                 database_id: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller, database_id)
        self.frame = frame if frame else PropertyFrame()
        self.alias = database_alias
        self.pagelist = PageList(self)
        self.agents.update(pagelist=self.pagelist)

    @property
    def master_name(self):
        return self.alias

    def retrieve(self):
        gateway = RetrieveDatabase(self)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def preview(self):
        return {**self.pagelist.preview()}

    def execute(self):
        self.pagelist.execute()

    def fully_read_rich(self):
        pass

    def fully_read(self):
        pass


class PageList(PointEditor):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame
        self._normal = NormalPageListContainer(self)
        self._new = NewPageListContainer(self)
        self.query_form = Query(self)

    def __bool__(self):
        any([self._normal, self._new])

    def __iter__(self):
        return iter(self.values())

    @property
    def by_id(self) -> dict[str, TabularPageBlock]:
        return self._normal.by_id

    def __getitem__(self, page_id: str):
        return self.by_id[page_id]

    def keys(self):
        return self.by_id.keys()

    def values(self) -> list[TabularPageBlock]:
        return self._normal.values + self._new.values

    @property
    def by_title(self) -> dict[str, TabularPageBlock]:
        return {**self._normal.by_title, **self._new.by_title}

    def by_index(self, prop_name: str) -> dict[str, TabularPageBlock]:
        try:
            return {page.props.read_of(prop_name): page
                    for page in self.values()}
        except TypeError:
            page_object = self.values()[0]
            pprint(f"key : {page_object.props.read_of(prop_name)}")
            pprint(f"value : {page_object.master_id}")
            raise TypeError

    def by_prop(self, prop_name: str) -> dict[str, list[TabularPageBlock]]:
        res = defaultdict(list)
        for page in self.values():
            res[page.props.read_of(prop_name)].append(page)
        return res

    def new_tabular_page(self):
        return self._new.new_tabular_page()

    def run_query(self, page_size=0):
        response = self.query_form.execute(page_size=page_size)
        parser = PageListParser(response)
        self._normal.apply_parser(parser)
        self.query_form = Query(self)

    def preview(self):
        return {'pages': self._normal.preview(),
                'new_pages': self._new.preview()}

    def execute(self):
        self._normal.execute()
        response = self._new.execute()
        self._normal.values.extend(response)


class NormalPageListContainer(BridgeEditor):
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


class NewPageListContainer(BridgeEditor):
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
            child.fetch()  # individual tabular_page will update themselves.
        res = self.values.copy()
        self.values.clear()
        return res


class TabularPageBlock(ChildBearingBlock):
    def __init__(self, caller: Union[Editor, NormalPageListContainer],
                 page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller=caller, block_id=page_id)
        self.frame = frame if frame else caller.frame \
            if hasattr(caller, 'frame') else PropertyFrame()
        self.props = TabularProperty(caller=self)
        self.agents.update(props=self.props)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    def preview(self):
        return {'tabular': self.props.preview(),
                'children': self.children.preview()}

    def execute(self):
        self.props.execute()
        self.children.execute()

    def fully_read(self):
        return {'type': 'page',
                'tabular': self.props.read_of_all(),
                'children': self.children.reads()}

    def fully_read_rich(self):
        return {'type': 'page',
                'tabular': self.props.read_rich_of_all(),
                'children': self.children.reads_rich()}
