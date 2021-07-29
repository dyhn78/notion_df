from __future__ import annotations
from collections import defaultdict
from pprint import pprint
from typing import Optional

from .page import TabularPage
from ..parse import PageListParser, BlockChildrenParser
from ..read import Query, RetrieveBlockChildren


class PageList:
    unit_class = TabularPage

    def __init__(self, parsed_query: PageListParser, parent_id: str):
        self.parent_id = parent_id
        self._id_by_unique_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

        self.values: list[TabularPage] \
            = [self.unit_class(parsed_page, parent_id)
               for parsed_page in parsed_query.values]
        self.page_by_id: dict[str, TabularPage] \
            = {page.page_id: page for page in self.values}

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    @classmethod
    def query(cls, query: Query, page_size=0):
        response = query.execute(page_size=page_size)
        database_id = query.page_id
        parsed_query = PageListParser.from_query_response(response)
        return cls(parsed_query, database_id)

    @classmethod
    def query_and_retrieve_childrens(cls, query: Query, page_size=0):
        self = cls.query(query, page_size=page_size)
        request_queue = []
        result_queue = []
        for page in self.values:
            request_queue.append(RetrieveBlockChildren(page.page_id))
        for request in request_queue:
            page_id = request.block_id
            result_queue.append([page_id, request.execute()])
        for result in result_queue:
            page_id, response = result
            page = self.page_by_id[page_id]
            parsed_blocklist = BlockChildrenParser.from_response(response)
            page.children.fetch(parsed_blocklist.children)
        return self

    def apply(self):
        result = []
        for page_object in self.values:
            if page_object:
                result.append(page_object.apply())
        return result

    def execute(self):
        result = []
        for page_object in self.values:
            res = page_object.execute()
            if res:
                result.append(res)
        return result

    @property
    def id_by_unique_title(self) -> dict[dict]:
        if self._id_by_unique_title is None:
            self._id_by_unique_title = {page_object.title: page_object.page_id
                                        for page_object in self.values}
        return self._id_by_unique_title

    def id_by_index(self, prop_name) -> dict[dict]:
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
        return self._id_by_index[prop_name]

    def ids_by_prop(self, prop_name) -> dict[list[dict]]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self.values:
                res[page_object.props.read[prop_name]].append(page_object.page_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name]
