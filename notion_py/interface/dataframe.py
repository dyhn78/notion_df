from __future__ import annotations
from collections import defaultdict
from typing import Optional, Any
from pprint import pprint

from notion_py.interface import TabularPage
from notion_py.gateway.parse import PageListParser, BlockChildrenParser
from notion_py.gateway.read import Query, RetrieveBlockChildren


class PropertyFrame:
    def __init__(self, values=None):
        if type(values) == tuple:
            prop_name, prop_value = values
        elif type(values) == str:
            prop_name = values
            prop_value = None
        else:
            raise AssertionError(f'Invalid PropertyFrame: {values}')
        self.name = prop_name
        self.value = prop_value


class DataFrame:
    def __init__(self, database_id: str,
                 database_name: str,
                 properties: Optional[dict[str, Any]] = None,
                 unit=TabularPage):
        self.database_id = database_id
        self.database_name = database_name
        self.props = {key: PropertyFrame(value) for key, value in properties.items()}
        self.unit = unit

    def execute_query(self, page_size=0) -> PageList:
        query = self.make_query()
        return self.insert_query(query, page_size=page_size)

    def make_query(self):
        return Query(self.database_id)

    def insert_query(self, query: Query, page_size=0):
        response = query.execute(page_size=page_size)
        parsed_query = PageListParser.from_query_response(response)
        return self._pagelist()(self, parsed_query, self.unit)

    @staticmethod
    def _pagelist():
        return PageList


class PageList:
    PROP_NAME = {}

    def __init__(self, dataframe: DataFrame,
                 parsed_query: PageListParser, unit=TabularPage):
        self.dataframe = dataframe
        self.values: list[TabularPage] \
            = [unit(parsed_page, self.PROP_NAME, self.dataframe.database_id)
               for parsed_page in parsed_query.values]

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def __iter__(self):
        return iter(self.values)

    def __len__(self):
        return len(self.values)

    def retrieve_childrens(self):
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

    def retrieve_descendants(self):
        pass  # TODO

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
