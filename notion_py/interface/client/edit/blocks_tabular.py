from __future__ import annotations
from typing import Optional
from collections import defaultdict
from pprint import pprint

from .blocks_inline import InlinePageContents, Block, BlockChildren
from .struct import BridgeEditor, MainEditor, GroundEditor
from ..frame import PropertyUnit, PropertyFrame
from ...api_format.encode import TabularPropertybyKey, PropertyUnitWriter
from ...api_format.parse import PageListParser, PageParser, DatabaseParser
from ...gateway import Query, RetrievePage, UpdatePage, RetrieveDatabase


class TabularPage(Block):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[PageList] = None):
        super().__init__(page_id, caller=caller)
        self.props = TabularProperty(caller=self)
        self.agents.update(props=self.props)
        self.title = ''
        if frame is None:
            if caller is not None:
                frame = caller.frame
            else:
                frame = PropertyFrame()
        self.frame = frame

    def fetch_retrieve(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)

        self.frame.fetch_parser(parser)
        self.props.fetch_parser(parser)
        self.title = parser.title
        return self.props


class TabularProperty(GroundEditor, TabularPropertybyKey):
    def __init__(self, caller: TabularPage):
        super().__init__(caller)
        self.gateway = UpdatePage(caller.master_id)
        self.frame = caller.frame

        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def fetch_parser(self, page_parser: PageParser):
        self._read_plain = page_parser.prop_values
        self._read_rich = page_parser.prop_rich_values
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

    def read_all(self):
        return self._read_full

    def read_all_keys(self):
        return {key: self._read_full[self._prop_name(key)] for key in self.frame}

    def read_at(self, prop_name: str):
        return self._read_plain[prop_name]

    def read_rich_at(self, prop_name: str):
        return self._read_rich[prop_name]

    def read_on(self, prop_key: str):
        return self.read_at(self._prop_name(prop_key))

    def read_rich_on(self, prop_key: str):
        return self.read_rich_at(self._prop_name(prop_key))

    def _push(self, prop_name: str, carrier: PropertyUnitWriter) \
            -> Optional[PropertyUnitWriter]:
        if self.enable_overwrite or self.eval_empty(self.read_at(prop_name)):
            return self.gateway.apply_prop(carrier)
        return None

    def _prop_name(self, prop_key: str):
        return self.frame.key_to_name[prop_key]

    def _prop_type(self, prop_name: str):
        return self.frame[prop_name].type

    @staticmethod
    def eval_empty(value):
        return eval_empty(value)


class PageList(BridgeEditor):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.values: list[TabularPage] = []
        self.frame = caller.frame

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def fetch_parser(self, pagelist_parser: PageListParser):
        for page_parser in pagelist_parser:
            child_page = TabularPage(page_parser.page_id, caller=self)
            child_page.props.fetch_parser(page_parser)
            self.values.append(child_page)
        if pagelist_parser:
            self.frame.fetch_parser(pagelist_parser[0])

    def page_by_id(self, page_id: str) -> TabularPage:
        if self._page_by_id is None:
            self._page_by_id: dict[str, TabularPage] \
                = {page.master_id: page for page in self.values}
        return self._page_by_id[page_id]

    def id_by_title(self, page_title: str) -> str:
        if self._id_by_title is None:
            self._id_by_title = {page_object.title: page_object.master_id
                                 for page_object in self.values}
        return self._id_by_title[page_title]

    def id_by_index(self, prop_name: str, index_value) -> str:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props.read_at(prop_name): page_object.master_id
                       for page_object in self.values}
            except TypeError:
                page_object = self.values[0]
                pprint(f"key : {page_object.props.read_at(prop_name)}")
                pprint(f"value : {page_object.master_id}")
                raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name][index_value]

    def ids_by_prop(self, prop_name: str, prop_value) -> list[str]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self.values:
                res[page_object.props.read_at(prop_name)].append(page_object.master_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name][prop_value]


class Database(MainEditor):
    def __init__(self, database_id: str,
                 database_name: str,
                 frame_units: Optional[list[PropertyUnit]] = None,
                 caller: Optional[BlockChildren] = None):
        super().__init__(database_id, caller)
        self.name = database_name
        self.frame = PropertyFrame(frame_units)
        self.pagelist_value = PageList(self)
        self.agents.update(pagelist=self.pagelist_value)

    def fetch_query(self, page_size=0):
        gateway = Query(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = PageListParser(response)
        self.pagelist_value.fetch_parser(parser)

    def fetch_retrieve(self):
        gateway = RetrieveDatabase(self.master_id)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)
