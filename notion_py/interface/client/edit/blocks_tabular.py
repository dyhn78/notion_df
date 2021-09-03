from __future__ import annotations
from typing import Optional
from collections import defaultdict
from pprint import pprint

from .blocks_inline import NewBlockChildren, SupportedBlock
from ...struct import \
    BridgeEditor, MasterEditor, GroundEditor, \
    PropertyUnit, PropertyFrame
from .eval_empty import eval_empty
from ...api_format.encode import TabularPropertybyKey, PropertyEncoder
from ...api_format.parse import PageListParser, PageParser, DatabaseParser
from ...gateway import Query, RetrievePage, UpdatePage, RetrieveDatabase, CreatePage


class Database(MasterEditor):
    def __init__(self, database_id: str,
                 database_name: str,
                 frame_units: Optional[list[PropertyUnit]] = None,
                 caller: Optional[NewBlockChildren] = None):
        super().__init__(database_id, caller)
        self.name = database_name
        self.frame = PropertyFrame(frame_units)
        self.pagelist = NormalPageList(self)
        self.new_pagelist = NewPageList(self)
        self.agents.update(pagelist=self.pagelist,
                           new_pagelist=self.new_pagelist)

    def fetch_query(self, page_size=0):
        gateway = Query(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = PageListParser(response)
        self.pagelist.apply_parser(parser)

    def fetch_retrieve(self):
        gateway = RetrieveDatabase(self.master_id)
        response = gateway.execute()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)

    def unpack(self):
        pass

    def execute(self):
        self.pagelist.execute()
        response = self.new_pagelist.execute()
        self.pagelist.values.extend(response)


class DatabaseSchema(GroundEditor):
    pass  # TODO, in the far future


class TabularPageBlock(SupportedBlock):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[NormalPageList] = None):
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

    def retrieve_this(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def apply_page_parser(self, parser: PageParser):
        self.title = parser.title
        if not self.master_id:
            self.master_id = parser.page_id
        self.frame.fetch_parser(parser)
        self.props.apply_page_parser(parser)

    def read(self):
        return {'type': 'page',
                'props': self.props.read_all_plain(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'type': 'page',
                'props': self.props.read_all_rich(),
                'children': self.children.reads_rich()}

    def unpack(self):
        return {'props': self.props.unpack(),
                'children': self.children.unpack(),
                'new_children': self.new_children.unpack()}

    def execute(self):
        """this is identical(except the first line) to InlinePageBlock.execute()"""
        response = self.props.execute()
        if self.master_id:
            parser = PageParser.parse_update(response)
            self.apply_page_parser(parser)
        else:
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
            self.props.reset_gateway()
            self.new_children.gateway.parent_id = self.master_id
        self._execute_children_agents()


class TabularProperty(GroundEditor, TabularPropertybyKey):
    def __init__(self, caller: TabularPageBlock):
        super().__init__(caller)
        assert isinstance(self.caller, TabularPageBlock)
        if self.caller.is_yet_not_created:
            self.gateway = CreatePage(self.caller.parent_id, under_database=True)
        else:
            self.gateway = self._default_gateway()
        self.frame = self.caller.frame
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def reset_gateway(self):
        self.gateway = self._default_gateway()

    def _default_gateway(self):
        return UpdatePage(self.caller.master_id)

    def apply_page_parser(self, parser: PageParser):
        if not self.gateway.page_id:
            self.gateway.page_id = parser.page_id
        self._read_plain = parser.prop_values
        self._read_rich = parser.prop_rich_values
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

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

    def _push(self, prop_name: str, carrier: PropertyEncoder) \
            -> Optional[PropertyEncoder]:
        if self.enable_overwrite or eval_empty(self.read_at(prop_name)):
            return self.gateway.apply_prop(carrier)
        return None

    def _name_at(self, prop_key: str):
        return self.frame.by_key[prop_key].name

    def _type_of(self, prop_name: str):
        return self.frame.by_name[prop_name].type


class NormalPageList(BridgeEditor):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.values: list[TabularPageBlock] = []
        self.frame = caller.frame

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def apply_parser(self, pagelist_parser: PageListParser):
        for page_parser in pagelist_parser:
            child_page = TabularPageBlock(page_parser.page_id, caller=self)
            child_page.props.apply_page_parser(page_parser)
            self.values.append(child_page)
        if pagelist_parser:
            self.frame.fetch_parser(pagelist_parser[0])

    def page_by_id(self, page_id: str) -> TabularPageBlock:
        if self._page_by_id is None:
            self._page_by_id: dict[str, TabularPageBlock] \
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


class NewPageList(BridgeEditor):
    def __init__(self, caller: Database):
        super().__init__(caller)
        assert isinstance(self.caller, Database)
        self.values: list[TabularPageBlock] = []

    def new_tabular_page(self):
        child = TabularPageBlock.create_new(self)
        self.values.append(child)
        # for debugging
        if id(child) != id(self.values[-1]):
            print('lol')
        return child

    def execute(self):
        # individual tabular_page will update themselves.
        super().execute()
        res = self.values.copy()
        self.values.clear()
        return res
