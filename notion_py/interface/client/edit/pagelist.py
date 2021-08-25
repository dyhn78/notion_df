from __future__ import annotations
from typing import Optional
from collections import defaultdict
from pprint import pprint

from .tabular_page import TabularPage
from ..frame import PropertyUnit, PropertyFrame
from notion_py.interface.common import Requestor
from notion_py.interface.gateway.others import GetBlockChildren
from ..parse import PageListParser, BlockChildrenParser


class PageList(Requestor):
    def __init__(self, database_id: str,
                 database_name: str,
                 frame_units: Optional[list[PropertyUnit]] = None):
        self.database_id = database_id
        self.database_name = database_name
        self.frame = PropertyFrame(frame_units)
        self.values = None

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def fetch_query(self, query_response: dict):
        parsed_query = PageListParser.fetch_query(query_response)
        self.values = parsed_query

    def unpack(self):
        result = []
        for page_object in self.values:
            if page_object:
                result.append(page_object.unpack())
        return result

    def execute(self):
        result = []
        for page_object in self.values:
            res = page_object.execute()
            if res:
                result.append(res)
        return result

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def retrieve_childrens(self):
        request_queue = []
        result_queue = []
        for page in self.values:
            request_queue.append(GetBlockChildren(page.page_id))
        for request in request_queue:
            page_id = request.block_id
            result_queue.append([page_id, request.execute()])
        for result in result_queue:
            page_id, response = result
            page = self.page_by_id(page_id)
            children_parser = BlockChildrenParser(response)
            page.children.fetch(children_parser.values)

    def retrieve_descendants(self):
        pass  # TODO

    def page_by_id(self, page_id: str) -> TabularPage:
        if self._page_by_id is None:
            self._page_by_id: dict[str, TabularPage] \
                = {page.page_id: page for page in self.values}
        return self._page_by_id[page_id]

    def id_by_title(self, page_title: str) -> str:
        if self._id_by_title is None:
            self._id_by_title = {page_object.title: page_object.page_id
                                 for page_object in self.values}
        return self._id_by_title[page_title]

    def id_by_index(self, prop_name: str, index_value) -> str:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props.read[prop_name]: page_object.page_id
                       for page_object in self.values}
            except TypeError:
                try:
                    res = {page_object.props.read[prop_name][0]: page_object.page_id
                           for page_object in self.values}
                except TypeError:
                    page_object = self.values[0]
                    pprint(f"key : {page_object.props.read[prop_name]}")
                    pprint(f"value : {page_object.page_id}")
                    raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name][index_value]

    def ids_by_prop(self, prop_name: str, prop_value) -> list[str]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self.values:
                res[page_object.props.read[prop_name]].append(page_object.page_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name][prop_value]
