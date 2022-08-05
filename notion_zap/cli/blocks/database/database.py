from __future__ import annotations

from pprint import pprint
from typing import Union, Optional, Iterator, Callable, Any, Hashable

from notion_client import APIResponseError

from notion_zap.cli.blocks.shared.children import Children, BlockWithChildren
from notion_zap.cli.core import PropertyFrame
from notion_zap.cli.core.exceptions import InvalidBlockTypeError
from notion_zap.cli.core.registry_table import IndexTable, ClassifyTable
from ..row.main import PageRow
from ..shared.with_items import ItemChildren
from ...core.base import RootSpace
from ...gateway.parsers import DatabaseParser
from ...gateway.requestors import Query, RetrieveDatabase
from ...utility import url_to_id


class Database(BlockWithChildren):
    def __init__(self, caller: Union[RootSpace, ItemChildren],
                 id_or_url: str,
                 alias: Hashable = None,
                 frame: Optional[PropertyFrame] = None, ):
        self.title = ''
        self.frame = frame if frame else PropertyFrame()
        BlockWithChildren.__init__(self, caller, id_or_url, alias)
        self.rows = RowChildren(self)

    @property
    def block_name(self):
        return self.title

    @property
    def children(self):
        return self.rows

    def _fetch_children(self, request_size=0):
        """randomly query with the amount of <request_size>."""
        query = self.rows.open_query()
        query.execute(request_size)

    def retrieve(self):
        requestor = RetrieveDatabase(self)
        response = requestor.execute_silent()
        parser = DatabaseParser(response)
        self.frame.fetch_parser(parser)
        requestor.print_comments()

    def read_contents(self) -> dict[str, Any]:
        pass

    def richly_read_contents(self) -> dict[str, Any]:
        pass


class RowChildren(Children):
    def __init__(self, caller: Database):
        self.frame = caller.frame if caller.frame else PropertyFrame()
        Children.__init__(self, caller)
        self.caller = caller

        from .save_agents import RowChildrenUpdater, RowChildrenCreator
        self._updater = RowChildrenUpdater(self)
        self._creator = RowChildrenCreator(self)

    def __iter__(self) -> Iterator[PageRow]:
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

    def contain(self, child: PageRow):
        if isinstance(child, PageRow):
            if child.block_id:
                self._updater.attach_page(child)
            else:
                self._creator.attach_page(child)
        else:
            raise InvalidBlockTypeError(child)

    def release(self, child: PageRow):
        if child.block_id:
            self._updater.detach_page(child)
        else:
            self._creator.detach_page(child)

    def open_query(self) -> QueryWithCallback:
        def callback(response):
            return self._updater.apply_query_response(response)

        return QueryWithCallback(self, self.frame, callback)

    def fetch_page(self, id_or_url: str):
        """this will first try to search the page in local base,
        then make a request (RetrievePage).
        returns child_page if succeed, otherwise returns None."""
        page_id = url_to_id(id_or_url)
        if page := self.by_id.get(page_id):
            return page
        page = self.open_page(page_id)
        try:
            page.retrieve()
            return page
        except APIResponseError:
            page.caller = None
            return None

    @property
    def by_id(self) -> IndexTable[str, PageRow]:
        return super().by_id

    @property
    def by_title(self) -> ClassifyTable[str, PageRow]:
        return super().by_title

    def index_by_key(self, prop_key: str) -> IndexTable[Hashable, PageRow]:
        flag = False
        if not isinstance(self.root.by_keys.get(prop_key), IndexTable):
            self.root.by_keys[prop_key] = IndexTable()
            flag = True
        if not isinstance(self.by_keys.get(prop_key), IndexTable):
            self.by_keys[prop_key] = IndexTable()
            flag = True
        if flag:
            for page in self.list_all():
                page.register_a_key(prop_key)
        return self.by_keys[prop_key]

    def index_by_tag(self, prop_tag: str) -> IndexTable[Hashable, PageRow]:
        flag = False
        if not isinstance(self.root.by_tags.get(prop_tag), IndexTable):
            self.root.by_tags[prop_tag] = IndexTable()
            flag = True
        if not isinstance(self.by_tags.get(prop_tag), IndexTable):
            self.by_tags[prop_tag] = IndexTable()
            flag = True
        if flag:
            for page in self.list_all():
                page.register_a_tag(prop_tag)
        return self.by_tags[prop_tag]

    def classify_by_key(self, prop_key: str) -> ClassifyTable[Hashable, PageRow]:
        flag = False
        if not isinstance(self.root.by_keys.get(prop_key), ClassifyTable):
            self.root.by_keys[prop_key] = ClassifyTable()
            flag = True
        if not isinstance(self.by_keys.get(prop_key), ClassifyTable):
            self.by_keys[prop_key] = ClassifyTable()
            flag = True
        if flag:
            for page in self.list_all():
                page.register_a_key(prop_key)
        return self.by_keys[prop_key]

    def classify_by_tag(self, prop_tag: str) -> ClassifyTable[Hashable, PageRow]:
        flag = False
        if not isinstance(self.root.by_tags.get(prop_tag), ClassifyTable):
            self.root.by_keys[prop_tag] = ClassifyTable()
            flag = True
        if not isinstance(self.by_tags.get(prop_tag), ClassifyTable):
            self.by_tags[prop_tag] = ClassifyTable()
            flag = True
        if flag:
            for page in self.list_all():
                page.register_a_tag(prop_tag)
        return self.by_tags[prop_tag]


class QueryWithCallback(Query):
    def __init__(self, editor: RowChildren, frame: PropertyFrame,
                 execute_callback: Callable[[Any], list[PageRow]]):
        super().__init__(editor, frame)
        self.callback = execute_callback

    def execute(self, request_size=0, print_heads: int = None):
        response = super().execute(request_size)
        pages = self.callback(response)

        if print_heads is None:
            print_heads = self.root.print_heads
        if pages and print_heads:
            heads = [(page.title, page.block_url) for page in pages[:print_heads]]
            if pages[print_heads:]:
                # noinspection PyTypeChecker
                heads.append('...')
            try:
                pprint(heads)
            except AttributeError:
                # pprint causes error on pythonw.exe
                pass
        return pages
