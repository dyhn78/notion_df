from __future__ import annotations
from collections import defaultdict
from pprint import pprint
from typing import Union, Optional, Iterator, Callable, Any

from notion_client import APIResponseError

from notion_zap.cli.gateway import parsers, requestors
from notion_zap.cli.structs import PropertyFrame
from ..row.leader import (
    PageRow, IndexTable, ClassifyTable, IndexKeyRegisterer,
    IndexTagRegisterer, ClassifyKeyRegisterer, ClassifyTagRegisterer)
from ..common.with_children import Children, ChildrenBearer
from ..common.with_items import ItemChildren
from ..structs.leaders import Root


class Database(ChildrenBearer):
    def __init__(self, caller: Union[Root, ItemChildren],
                 id_or_url: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller, id_or_url)
        self.caller = caller

        self.alias = database_alias
        self.root.by_alias[self.alias] = self
        self.frame = frame if frame else PropertyFrame()

        self.rows = RowChildren(self)

        from .schema import DatabaseSchema
        self.schema = DatabaseSchema(self)

    @property
    def payload(self):
        return self.schema

    @property
    def children(self):
        return self.rows

    @property
    def block_name(self):
        return self.alias

    def _fetch_children(self, request_size=0):
        """randomly query with the amount of <request_size>."""
        query = self.rows.open_query()
        query.execute(request_size)

    def retrieve(self):
        requestor = requestors.RetrieveDatabase(self)
        response = requestor.execute_silent()
        parser = parsers.DatabaseParser(response)
        self.frame.fetch_parser(parser)
        requestor.print_comments()

    def save(self):
        self.payload.save()
        if not self.archived:
            self.children.save()
        return self


class RowChildren(Children):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame

        from .followers import RowChildrenUpdater, RowChildrenCreator
        self._updater = RowChildrenUpdater(self)
        self._creator = RowChildrenCreator(self)

        self._index_tables: dict[str, IndexTable] = defaultdict(IndexTable)
        self._classify_tables: dict[str, ClassifyTable] = defaultdict(ClassifyTable)

    def __iter__(self) -> Iterator[PageRow]:
        return self.iter_all()

    def iter_all(self) -> Iterator[PageRow]:
        return iter(self.list_all())

    def list_all(self) -> list[PageRow]:
        return self._updater.values + self._creator.values

    def save(self):
        self._updater.save()
        response = self._creator.save()
        self._updater.values.extend(response)

    def save_required(self):
        return (self._updater.save_required()
                or self._creator.save_required())

    def open_page(self, page_id: str):
        return PageRow(self, page_id, frame=self.frame)

    def open_new_page(self):
        return self.open_page('')

    def _deposit(self, child: PageRow):
        if child.block_id:
            self._updater.attach_page(child)
        else:
            self._creator.attach_page(child)

    def detach(self, child: PageRow):
        super().detach(child)
        if child.block_id:
            self._updater.detach_page(child)
        else:
            self._creator.detach_page(child)

    def open_query(self) -> QueryWithCallback:
        def callback(response):
            return self._updater.apply_query_response(response)

        return QueryWithCallback(self, self.frame, callback)

    def fetch(self, page_id: str):
        """this will first try to search the page in local base,
        then make a request (RetrievePage).
        returns child_page if succeed, otherwise returns None."""
        if page := self.by_id.get(page_id):
            return page
        page = self.open_page(page_id)
        try:
            page.props.retrieve()
            return page
        except APIResponseError:
            page.close()
            return None

    @property
    def by_id(self) -> dict[str, PageRow]:
        return self._by_id

    @property
    def by_title(self) -> dict[str, list[PageRow]]:
        return self._by_title

    def by_value_of(self, prop_key: str):
        res = defaultdict(list)
        for page in self.list_all():
            res[page.props.read_key(prop_key)].append(page)
        return res

    def by_value_at(self, prop_tag: str):
        return self.by_value_of(self.frame.key_of(prop_tag))

    def by_idx_at(self, prop_tag: str):
        return self.by_idx_of(self.frame.key_of(prop_tag))

    def by_idx_of(self, prop_key: str):
        try:
            res = {}
            for page in self.list_all():
                res[page.props.read_key(prop_key)] = page
            return res
        except TypeError:
            page_object = self.list_all()[0]
            pprint(f"key : {page_object.props.read_key(prop_key)}")
            pprint(f"value : {page_object.block_id}")
            raise TypeError

    def create_index_by_key(self, prop_key: str):
        if prop_key not in self.key_tables:
            self.key_tables[prop_key] = IndexTable()
        for page in self.list_all():
            if prop_key in page.regs_key:
                reg = page.regs_key[prop_key]
            else:
                reg = IndexKeyRegisterer(page, prop_key)
            reg.register_to_root_and_parent()
        return self.key_tables[prop_key]

    def create_index_by_tag(self, prop_tag: str):
        if prop_tag not in self.tag_tables:
            self.tag_tables[prop_tag] = IndexTable()
        for page in self.list_all():
            if prop_tag in page.regs_tag:
                reg = page.regs_tag[prop_tag]
            else:
                reg = IndexTagRegisterer(page, prop_tag)
            reg.register_to_root_and_parent()
        return self.tag_tables[prop_tag]

    def classify_by_key(self, prop_key: str):
        if prop_key not in self.key_tables:
            self.key_tables[prop_key] = ClassifyTable()
        for page in self.list_all():
            if prop_key in page.regs_key:
                reg = page.regs_key[prop_key]
            else:
                reg = ClassifyKeyRegisterer(page, prop_key)
            reg.register_to_root_and_parent()
        return self.tag_tables[prop_key]

    def classify_by_tag(self, prop_tag: str):
        if prop_tag not in self.tag_tables:
            self.tag_tables[prop_tag] = ClassifyTable()
        for page in self.list_all():
            if prop_tag in page.regs_tag:
                reg = page.regs_tag[prop_tag]
            else:
                reg = ClassifyTagRegisterer(page, prop_tag)
            reg.register_to_root_and_parent()
        return self.tag_tables[prop_tag]


class QueryWithCallback(requestors.Query):
    def __init__(self, editor: RowChildren, frame: PropertyFrame,
                 execute_callback: Callable[[Any], list[PageRow]]):
        super().__init__(editor, frame)
        self.callback = execute_callback

    def execute(self, request_size=0, print_heads=0):
        response = super().execute(request_size)
        pages = self.callback(response)
        if pages and print_heads:
            heads = [(page.title, page.block_url) for page in pages[:print_heads]]
            if pages[print_heads:]:
                heads.append(('...', '...'))
            try:
                pprint(heads)
            except AttributeError:
                # pprint causes error on pythonw.exe
                pass
        return pages
