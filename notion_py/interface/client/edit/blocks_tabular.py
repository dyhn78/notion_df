from __future__ import annotations

from collections import defaultdict
from pprint import pprint
from typing import Optional

from .blocks_inline import NewBlockChildrenContainer, SupportedBlock
from .eval_empty import eval_empty
from ...api_format.encode import TabularPropertybyKey, PropertyEncoder
from ...api_format.parse import PageListParser, PageParser, DatabaseParser
from ...gateway import RetrievePage, UpdatePage, RetrieveDatabase, CreatePage
from ...struct import \
    Editor, BridgeEditor, MasterEditor, GroundEditor, PropertyFrame


class Database(MasterEditor):
    def __init__(self, database_id: str,
                 database_name: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[NewBlockChildrenContainer] = None):
        super().__init__(database_id, caller)
        self.frame = frame if frame else PropertyFrame()
        self.name = database_name
        self.yet_not_created = False
        self.pagelist = PageList(self)
        self.agents.update(pagelist=self.pagelist)

    def sync_master_id(self):
        self.pagelist.sync_master_id()

    def retrieve(self):
        gateway = RetrieveDatabase(self.master_id)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def unpack(self):
        return {**self.pagelist.unpack()}

    def execute(self):
        self.pagelist.execute()


class DatabaseSchema(GroundEditor):
    pass  # TODO, in the far future


class PageList(Editor):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame
        self._normal = NormalPageListContainer(self)
        self._new = NewPageListContainer(self)

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def __bool__(self):
        any([self._normal, self._new])

    def sync_master_id(self):
        self._new.sync_master_id()

    def unpack(self):
        return {'pages': self._normal.unpack(),
                'new_pages': self._new.unpack()}

    def execute(self):
        self._normal.execute()
        response = self._new.execute()
        self._normal.values.extend(response)

    def page_by_id(self, page_id: str) -> TabularPageBlock:
        if self._page_by_id is None:
            self._page_by_id: dict[str, TabularPageBlock] \
                = {page.master_id: page for page in self._normal}
        return self._page_by_id[page_id]

    def id_by_title(self, page_title: str) -> str:
        if self._id_by_title is None:
            self._id_by_title = {page_object.title: page_object.master_id
                                 for page_object in self._normal}
        return self._id_by_title[page_title]

    def id_by_index(self, prop_name: str, index_value) -> str:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props.read_at(prop_name): page_object.master_id
                       for page_object in self._normal}
            except TypeError:
                page_object = self._normal[0]
                pprint(f"key : {page_object.props.read_at(prop_name)}")
                pprint(f"value : {page_object.master_id}")
                raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name][index_value]

    def ids_by_prop(self, prop_name: str, prop_value) -> list[str]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self._normal:
                res[page_object.props.read_at(prop_name)].append(page_object.master_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name][prop_value]


class TabularPageBlock(SupportedBlock):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[NormalPageListContainer] = None):
        super().__init__(page_id, caller=caller)
        self.frame = frame if frame else caller.frame
        self.props = TabularProperty(caller=self)
        self.agents.update(props=self.props)
        self.title = ''

    def sync_master_id(self):
        self.props.sync_master_id()
        self.children.sync_master_id()

    def unpack(self):
        return {'props': self.props.unpack(),
                'children': self.children.unpack()}

    def execute(self):
        """this is identical(except the first line) to InlinePageBlock.execute()"""
        self.props.execute()
        self.children.execute()

    def read(self):
        return {'type': 'page',
                'props': self.props.read_all_plain(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'type': 'page',
                'props': self.props.read_all_rich(),
                'children': self.children.reads_rich()}


class TabularProperty(GroundEditor, TabularPropertybyKey):
    def __init__(self, caller: TabularPageBlock):
        super().__init__(caller)
        self.caller = caller
        if self.caller.yet_not_created:
            self.gateway = CreatePage(self.caller.parent_id, under_database=True)
        else:
            self.gateway = UpdatePage(self.caller.master_id)
        self.frame = self.caller.frame
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def retrieve_this(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self.caller.yet_not_created:
            parser = PageParser.parse_create(response)
            self.gateway = UpdatePage(self.caller.master_id)
        else:
            parser = PageParser.parse_update(response)
        self.apply_page_parser(parser)

    def apply_page_parser(self, parser: PageParser):
        self.master_id = parser.page_id
        self.frame.fetch_parser(parser)
        self.caller.title = parser.title

        self._read_plain = parser.prop_values
        self._read_rich = parser.prop_rich_values
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

    def push_carrier(self, prop_name: str, carrier: PropertyEncoder) \
            -> Optional[PropertyEncoder]:
        if self.enable_overwrite or eval_empty(self.read_at(prop_name)):
            return self.gateway.apply_prop(carrier)
        return None

    def read_all_plain(self):
        return self._read_plain

    def read_all_rich(self):
        return self._read_rich

    def read_all_at(self):
        return self._read_full

    def read_all_of(self):
        return {key: self._read_full[self._name_at(key)] for key in self.frame}

    def read_at(self, prop_name: str):
        return self._read_plain[prop_name]

    def read_rich_at(self, prop_name: str):
        return self._read_rich[prop_name]

    def read_of(self, prop_key: str):
        return self.read_at(self._name_at(prop_key))

    def read_rich_of(self, prop_key: str):
        return self.read_rich_at(self._name_at(prop_key))

    def _name_at(self, prop_key: str):
        return self.frame.by_key[prop_key].name

    def _type_of(self, prop_name: str):
        return self.frame.by_name[prop_name].type


class NormalPageListContainer(BridgeEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.values: list[TabularPageBlock] = []
        self.frame = caller.frame

    def apply_parser(self, pagelist_parser: PageListParser):
        for page_parser in pagelist_parser:
            child_page = TabularPageBlock(page_parser.page_id, caller=self)
            child_page.props.apply_page_parser(page_parser)
            self.values.append(child_page)
        if pagelist_parser:
            self.frame.fetch_parser(pagelist_parser[0])


class NewPageListContainer(BridgeEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.caller = caller
        self.values: list[TabularPageBlock] = []

    def sync_master_id(self):
        if hasattr(self.master, 'yet_not_created'):
            if self.master.yet_not_created:
                for page in self.values:
                    page.sync_master_id()

    def new_tabular_page(self):
        page = TabularPageBlock.create_new(self)
        self.values.append(page)
        assert id(page) == id(self.values[-1])
        return page

    def execute(self):
        # individual tabular_page will update themselves.
        super().execute()
        res = self.values.copy()
        self.values.clear()
        return res
