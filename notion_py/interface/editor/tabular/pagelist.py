from __future__ import annotations

from collections import defaultdict
from pprint import pprint
from typing import Iterator

from notion_client import APIResponseError

from .page_row import PageRow
from .database import Database
from ..common.struct import MasterEditor
from ..common.with_children import BlockChildren
from ...parser import PageListParser
from ...requestor import Query


class PageList(BlockChildren):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame

        from .pagelist_agents import PageListUpdater, PageListCreator
        self._updater = PageListUpdater(self)
        self._creator = PageListCreator(self)

        self._by_id = {}
        self._by_title = defaultdict(list)

    @property
    def by_id(self) -> dict[str, PageRow]:
        return self._by_id

    @property
    def by_title(self) -> dict[str, list[PageRow]]:
        return self._by_title

    def list_all(self):
        return self._updater.blocks + self._creator.blocks

    def iter_all(self) -> Iterator[MasterEditor]:
        return iter(self.list_all())

    def fetch(self, request_size=0):
        query = self.open_query()
        query.execute(request_size)

    def open_query(self) -> Query:
        return Query(self, self.frame)

    def apply_query_response(self, response):
        parser = PageListParser(response)
        pages = self._updater.apply_pagelist_parser(parser)
        return pages

    def fetch_a_child(self, page_id: str):
        """this will first try to search the page in local base,
        then make a request (RetrievePage).
        returns child_page if succeed, otherwise returns None."""
        if page := self.by_id.get(page_id):
            return page
        page = self._updater.open_page(page_id)
        try:
            page.props.retrieve()
            return page
        except APIResponseError:
            self._updater.close_page(page)
            del page
            return None

    def create_page_row(self):
        return self._creator.create_page_row()

    def save(self):
        self._updater.save()
        response = self._creator.save()
        self._updater.blocks.extend(response)

    def save_info(self):
        return {'pages': self._updater.save_info(),
                'new_pages': self._creator.save_info()}

    def save_required(self):
        return (self._updater.save_required()
                or self._creator.save_required())

    def by_idx_value_of(self, prop_key: str):
        try:
            res = {}
            for page in self.list_all():
                res[page.props.read_of(prop_key)] = page
            return res
        except TypeError:
            page_object = self.list_all()[0]
            pprint(f"key : {page_object.props.read_of(prop_key)}")
            pprint(f"value : {page_object.block_id}")
            raise TypeError

    def by_value_of(self, prop_key: str):
        res = defaultdict(list)
        for page in self.list_all():
            res[page.props.read_of(prop_key)].append(page)
        return res

    def by_idx_value_at(self, prop_tag: str):
        return self.by_idx_value_of(self.frame.key_at(prop_tag))

    def by_value_at(self, prop_tag: str):
        return self.by_value_of(self.frame.key_at(prop_tag))
