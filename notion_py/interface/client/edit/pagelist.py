from __future__ import annotations
from typing import Optional
from collections import defaultdict
from pprint import pprint

from .editor_struct import MasterEditor, BridgeEditor
from .page_tabular import TabularPage
from ..frame import PropertyUnit, PropertyFrame
from ..parse import PageListParser
from ...gateway.query import Query


class Database(MasterEditor):
    def __init__(self, database_id: str,
                 database_name: str,
                 frame_units: Optional[list[PropertyUnit]] = None):
        super().__init__(database_id)
        self.pagelist = PageList(self)
        self.agents.update(pagelist=self.pagelist)

        self.name = database_name
        self.frame = PropertyFrame(frame_units)

    def fetch_query(self, page_size=0):
        gateway = Query(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = PageListParser(response)
        self.pagelist.fetch_parser(parser)


class PageList(BridgeEditor):
    def __init__(self, caller: Database):
        super().__init__(caller)
        assert isinstance(self.caller, Database)
        self.values: list[TabularPage] = []
        self.frame = self.caller.frame

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def fetch_parser(self, pagelist_parser: PageListParser):
        for page_parser in pagelist_parser:
            child_page = TabularPage(page_parser.page_id, self.frame, caller=self)
            child_page.props.fetch_parser(page_parser)
            self.values.append(child_page)

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
                res = {page_object.props.read[prop_name]: page_object.master_id
                       for page_object in self.values}
            except TypeError:
                try:
                    res = {page_object.props.read[prop_name][0]: page_object.master_id
                           for page_object in self.values}
                except TypeError:
                    page_object = self.values[0]
                    pprint(f"key : {page_object.props.read[prop_name]}")
                    pprint(f"value : {page_object.master_id}")
                    raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name][index_value]

    def ids_by_prop(self, prop_name: str, prop_value) -> list[str]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self.values:
                res[page_object.props.read[prop_name]].append(page_object.master_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name][prop_value]
