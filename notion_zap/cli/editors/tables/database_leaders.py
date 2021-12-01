from __future__ import annotations
from collections import defaultdict
from pprint import pprint
from typing import Union, Optional, Iterator, Callable, Any

from notion_client import APIResponseError

from notion_zap.cli.gateway import parsers, requestors
from notion_zap.cli.struct import PropertyFrame
from .. import BlockChildren, PageRow
from ..common.with_children import ChildrenBearer
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

        from .database_schema import DatabaseSchema
        self.schema = DatabaseSchema(self, id_or_url)

        self.rows = RowChildren(self)

    @property
    def payload(self):
        return self.schema

    @property
    def children(self):
        return self.rows

    @property
    def block_name(self):
        return self.alias

    def retrieve(self):
        requestor = requestors.RetrieveDatabase(self)
        response = requestor.execute_silent()
        parser = parsers.DatabaseParser(response)
        self.frame.fetch_parser(parser)
        requestor.print_comments()

    def _fetch_children(self, request_size=0):
        """randomly query with the amount of <request_size>."""
        query = self.rows.open_query()
        query.execute(request_size)

    def save(self):
        self.rows.save()

    def save_info(self):
        return {**self.rows.save_info()}

    def read(self):
        return {"rows": self.rows.by_title,
                "type": "database",
                "id": self.block_id}

    def richly_read(self):
        return self.read()


class RowChildren(BlockChildren):
    def __init__(self, caller: Database):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame

        from .database_followers import PageListUpdater, PageListCreator
        self.update = PageListUpdater(self)
        self.create = PageListCreator(self)

        self._by_id = {}
        self._by_title = defaultdict(list)

    def open_page(self, page_id: str):
        return PageRow(self, page_id, frame=self.frame)

    def create_page(self):
        return PageRow(self, '', frame=self.frame)

    def attach(self, page: PageRow):
        super().attach(page)
        if page.block_id:
            self.update.attach_page(page)
        else:
            self.create.attach_page(page)

    def detach(self, page: PageRow):
        super().detach(page)
        if page.block_id:
            self.update.detach_page(page)
        else:
            self.create.detach_page(page)

    def open_query(self) -> QueryWithCallback:
        def callback(response):
            return self.update.apply_query_response(response)

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
            self.detach(page)
            return None

    def save(self):
        self.update.save()
        response = self.create.save()
        self.update.blocks.extend(response)

    def save_info(self):
        return {'updated_rows': self.update.save_info(),
                'created_rows': self.create.save_info()}

    def save_required(self):
        return (self.update.save_required()
                or self.create.save_required())

    @property
    def by_id(self) -> dict[str, PageRow]:
        return self._by_id

    @property
    def by_title(self) -> dict[str, list[PageRow]]:
        return self._by_title

    def __iter__(self) -> Iterator[PageRow]:
        return self.iter_all()

    def iter_all(self) -> Iterator[PageRow]:
        return iter(self.list_all())

    def list_all(self) -> list[PageRow]:
        return self.update.blocks + self.create.blocks

    def by_value_of(self, prop_key: str):
        res = defaultdict(list)
        for page in self.list_all():
            res[page.props.read_key(prop_key)].append(page)
        return res

    def by_value_at(self, prop_tag: str):
        return self.by_value_of(self.frame.key_at(prop_tag))

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

    def by_idx_at(self, prop_tag: str):
        return self.by_idx_of(self.frame.key_at(prop_tag))


class QueryWithCallback(requestors.Query):
    def __init__(self, editor: RowChildren, frame: PropertyFrame,
                 execute_callback: Callable[[Any], list[PageRow]]):
        super().__init__(editor, frame)
        self.callback = execute_callback

    def execute(self, request_size=0, print_heads=0):
        # TODO: 수가 적으면 페이지 제목을 모두 (리스트 형태로) 프린트하게 수정
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
