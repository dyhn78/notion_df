from __future__ import annotations
from collections import defaultdict
from pprint import pprint

from .page import TabularPage
from ..parse import PageListParser, BlockChildrenParser
from ..read import Query, RetrieveBlockChildren


class PageList:
    PROP_NAME = {}

    def __init__(self, parsed_query: PageListParser, database_id: str, unit=TabularPage):
        self.frame = None
        self.database_id = database_id
        self.values: list[TabularPage] \
            = [unit(parsed_page, self.PROP_NAME, database_id)
               for parsed_page in parsed_query.values]

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    @classmethod
    def query_this(cls, query: Query, page_size=0, unit=TabularPage):
        response = query.execute(page_size=page_size)
        database_id = query.page_id
        parsed_query = PageListParser.from_query_response(response)
        return cls(parsed_query, database_id, unit)

    @classmethod
    def query_this_and_retrieve_childrens(cls, query: Query, page_size=0):
        self = cls.query_this(query, page_size=page_size)
        request_queue = []
        result_queue = []
        for page in self.values:
            request_queue.append(RetrieveBlockChildren(page.page_id))
        for request in request_queue:
            page_id = request.block_id
            result_queue.append([page_id, request.execute()])
        for result in result_queue:
            page_id, response = result
            page = self.page_by_id(page_id)
            parsed_blocklist = BlockChildrenParser.from_response(response)
            page.children.fetch(parsed_blocklist.children)
        return self

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

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
