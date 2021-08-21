from collections import defaultdict
from pprint import pprint

from .page import PageParser


class PageListParser:
    def __init__(self, page_parsers: list[PageParser], parent_id=''):
        self.parent_id = parent_id
        self.values = page_parsers
        self.search = PageListSearchAgent(self)

    @classmethod
    def from_query_response(cls, response: dict):
        return cls([PageParser.from_query_response(page_result)
                    for page_result in response['results']])


class PageListSearchAgent:
    def __init__(self, caller):
        self.caller = caller
        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)

    def page_by_id(self, page_id: str) -> PageParser:
        if self._page_by_id is None:
            self._page_by_id = {page_object.page_id: page_object.props
                                for page_object in self.caller.values}
        return self._page_by_id[page_id]

    def id_by_title(self, page_title: str) -> PageParser:
        if self._id_by_title is None:
            self._id_by_title = {page_object.title: page_object.page_id
                                 for page_object in self.caller.values}
        return self._id_by_title[page_title]

    def id_by_index(self, prop_name: str, page_index: str) -> dict[dict]:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props[prop_name]: page_object.page_id
                       for page_object in self.caller.values}
            except TypeError:
                try:
                    res = {page_object.props[prop_name][0]: page_object.page_id
                           for page_object in self.caller.values}
                except TypeError:
                    page_object = self.caller.values[0]
                    pprint(f"key : {page_object.props[prop_name]}")
                    pprint(f"value : {page_object.page_id}")
                    raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name][page_index]
