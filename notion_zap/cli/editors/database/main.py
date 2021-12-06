from __future__ import annotations
from pprint import pprint
from typing import Union, Optional, Iterator, Callable, Any, Hashable

from notion_client import APIResponseError

from notion_zap.cli.gateway import parsers, requestors
from notion_zap.cli.structs import PropertyFrame
from ..row.main import PageRow
from ..shared.with_children import Children, BlockWithChildren
from ..shared.with_items import ItemChildren
from ..structs.base_logic import RootGatherer
from ..structs.block_main import Payload
from ..structs.exceptions import InvalidBlockTypeError
from ..structs.registry_table import IndexTable, ClassifyTable


class Database(BlockWithChildren):
    def __init__(self, caller: Union[RootGatherer, ItemChildren],
                 id_or_url: str,
                 database_alias='',
                 frame: Optional[PropertyFrame] = None):
        self.frame = frame if frame else PropertyFrame()
        BlockWithChildren.__init__(self, caller, id_or_url)
        self.rows = RowChildren(self)
        self.alias = database_alias
        self.root.by_alias[self.alias] = self

    def _initalize_payload(self, block_id) -> Payload:
        from .schema import DatabaseSchema
        return DatabaseSchema(self, block_id)

    @property
    def schema(self):
        return self.payload

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
        self.schema.save()
        if not self.archived:
            self.children.save()
        return self


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

    def attach(self, child: PageRow):
        if isinstance(child, PageRow):
            if child.block_id:
                self._updater.attach_page(child)
            else:
                self._creator.attach_page(child)
        else:
            raise InvalidBlockTypeError(child)

    def detach(self, child: PageRow):
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
            page.caller = None
            return None

    @property
    def by_id(self) -> IndexTable[str, PageRow]:
        return super().by_id

    @property
    def by_title(self) -> ClassifyTable[str, PageRow]:
        return super().by_title

    def index_by_key(self, prop_key: str) -> IndexTable[Hashable, PageRow]:
        if isinstance(self.by_keys.get(prop_key), IndexTable):
            return self.by_keys[prop_key]
        else:
            if not self.root.by_keys.get(prop_key):
                self.root.by_keys[prop_key] = IndexTable()
            self.by_keys[prop_key] = IndexTable()
            for page in self.list_all():
                page.props.add_key_reg(prop_key)
            return self.by_keys[prop_key]

    def index_by_tag(self, prop_tag: str) -> IndexTable[Hashable, PageRow]:
        if isinstance(self.by_tags.get(prop_tag), IndexTable):
            return self.by_tags[prop_tag]
        else:
            if not self.root.by_tags.get(prop_tag):
                self.root.by_tags[prop_tag] = IndexTable()
            self.by_tags[prop_tag] = IndexTable()
            for page in self.list_all():
                page.props.add_tag_reg(prop_tag)
            return self.by_tags[prop_tag]

    def classify_by_key(self, prop_key: str) -> ClassifyTable[Hashable, PageRow]:
        if not isinstance(self.by_keys.get(prop_key), ClassifyTable):
            self.by_keys[prop_key] = ClassifyTable()
            for page in self.list_all():
                page.props.add_key_reg(prop_key)
        return self.by_tags[prop_key]

    def classify_by_tag(self, prop_tag: str) -> ClassifyTable[Hashable, PageRow]:
        if not isinstance(self.by_tags.get(prop_tag), ClassifyTable):
            self.by_tags[prop_tag] = ClassifyTable()
            for page in self.list_all():
                page.props.add_tag_reg(prop_tag)
        return self.by_tags[prop_tag]


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
                heads.append(...)
            try:
                pprint(heads)
            except AttributeError:
                # pprint causes error on pythonw.exe
                pass
        return pages
