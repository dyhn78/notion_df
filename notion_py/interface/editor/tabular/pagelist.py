from __future__ import annotations
from collections import defaultdict
from pprint import pprint

from .database import Database
from ..struct import PointEditor
from ...parser import PageListParser


class PageList(PointEditor):
    def __init__(self, caller: Database):
        from .pagelist_agents import PageListUpdater, PageListCreator
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame
        self._normal = PageListUpdater(self)
        self._new = PageListCreator(self)

    def __bool__(self):
        any([self._normal, self._new])

    def __iter__(self):
        return iter(self.elements)

    def __getitem__(self, page_id: str):
        return self.by_id[page_id]

    def open_query(self):
        from notion_py.interface.requestor import Query
        return Query(self, self.frame)

    @property
    def by_id(self):
        return self._normal.by_id

    @property
    def by_title(self):
        return {**self._normal.by_title, **self._new.by_title}

    def ids(self):
        return self.by_id.keys()

    @property
    def elements(self):
        return self._normal.values + self._new.values

    @property
    def descendants(self):
        res = []
        res.extend(self.elements)
        for page in self.elements:
            res.extend(page.sphere.descendants)
        return res

    def apply_query_response(self, response):
        parser = PageListParser(response)
        self._normal.apply_parser(parser)

    def fetch_descendants(self, depth=-1):
        if depth == 0:
            return
        for child in self.elements:
            child.sphere.fetch_descendants(depth=depth - 1)

    def create_tabular_page(self):
        return self._new.create_tabular_page()

    def preview(self):
        return {'pages': self._normal.preview(),
                'new_pages': self._new.preview()}

    def execute(self):
        self._normal.execute()
        response = self._new.execute()
        self._normal.values.extend(response)

    def by_idx_value_of(self, prop_key: str):
        try:
            res = {}
            for page in self.elements:
                res[page.props.read_of(prop_key)] = page
            return res
        except TypeError:
            page_object = self.elements[0]
            pprint(f"key : {page_object.props.read_of(prop_key)}")
            pprint(f"value : {page_object.master_id}")
            raise TypeError

    def by_value_of(self, prop_key: str):
        res = defaultdict(list)
        for page in self.elements:
            res[page.props.read_of(prop_key)].append(page)
        return res

    def by_idx_value_at(self, prop_tag: str):
        return self.by_idx_value_of(self.frame.key_at(prop_tag))

    def by_value_at(self, prop_tag: str):
        return self.by_value_of(self.frame.key_at(prop_tag))

    def set_overwrite_option(self, option: bool):
        for child in self.elements:
            child.set_overwrite_option(option)
