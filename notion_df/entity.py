from __future__ import annotations

import os
from collections.abc import Sequence, MutableMapping
from typing import Optional, TypeVar, Union, Generic, Iterator, final, Final, Any

from typing_extensions import Self

from notion_df.object.block import BlockType, BlockResponse, ChildPageBlockType, DatabaseResponse, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.property import PropertyKey, PageProperties, DatabaseProperties
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.request.request_core import Response_T
from notion_df.util.exception import NotionDfKeyError
from notion_df.util.misc import get_id, UUID


class BaseBlock(Generic[Response_T]):
    id: UUID

    # noinspection PyShadowingBuiltins
    def __new__(cls, namespace: Namespace, id_or_url: Union[UUID, str]):
        id = get_id(id_or_url) if isinstance(id_or_url, str) else id_or_url
        if id in namespace:
            return namespace[id]
        self = super().__new__(cls)
        namespace[id] = self
        return self

    def __init__(self, namespace: Namespace, id_or_url: Union[UUID, str]):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.namespace = namespace
        self.id = get_id(id_or_url)
        self._last_response: Optional[Response_T] = None

    @property
    def last_response(self) -> Optional[Response_T]:
        return self._last_response

    @last_response.setter
    def last_response(self, response: Response_T) -> None:
        if self._last_response is not None and self._last_response.timestamp > response.timestamp:
            return
        self._last_response = response

    @final
    def _get_parent(self, parent: ParentInfo) -> Union[Block, Database, Page, None]:
        if self.last_response is None:
            return None
        match parent.typename:
            case 'block_id':
                return Block(self.namespace, parent.id)
            case 'database_id':
                return Database(self.namespace, parent.id)
            case 'page_id':
                return Page(self.namespace, parent.id)
            case 'workspace':
                return None


BaseBlock_T = TypeVar('BaseBlock_T', bound=BaseBlock)


class Block(BaseBlock[BlockResponse]):
    @property
    def parent(self) -> Union[Page, Block, None]:
        return self._get_parent(self.last_response.parent)

    def _send_child_block_response_list(self, block_response_list: list[BlockResponse]) -> BlockChildren:
        block_list = []
        for block_response in block_response_list:
            block = Block(self.namespace, block_response.id)
            block.last_response = block_response
            block_list.append(block)
        return BlockChildren(block_list)

    def retrieve(self) -> Self:
        self.last_response = RetrieveBlock(self.namespace.token, self.id).execute(self.namespace.print_body)
        return self.last_response

    def retrieve_children(self) -> BlockChildren:
        block_response_list = RetrieveBlockChildren(self.namespace.token, self.id).execute(self.namespace.print_body)
        return self._send_child_block_response_list(block_response_list)

    def update(self, block_type: Optional[BlockType], archived: Optional[bool]) -> Self:
        self.last_response = UpdateBlock(self.namespace.token, self.id, block_type, archived).execute(
            self.namespace.print_body)
        return self.last_response

    def delete(self) -> Self:
        self.last_response = DeleteBlock(self.namespace.token, self.id).execute(self.namespace.print_body)
        return self.last_response

    def append_children(self, block_type_list: list[BlockType]) -> BlockChildren:
        block_response_list = AppendBlockChildren(self.namespace.token, self.id, block_type_list).execute(
            self.namespace.print_body)
        return self._send_child_block_response_list(block_response_list)

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.namespace.token, ParentInfo('page_id', self.id),
                                   properties, children, icon, cover).execute(self.namespace.print_body)
        page = Page(self.namespace, response_page.id)
        page.last_response = response_page
        return page

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        response_database = CreateDatabase(self.namespace.token, self.id, title, properties, icon, cover).execute(
            self.namespace.print_body)
        database = Database(self.namespace, response_database.id)
        database.last_response = response_database
        return database


class Database(BaseBlock[DatabaseResponse]):
    @property
    def parent(self) -> Union[Page, Block, None]:
        return self._get_parent(self.last_response.parent)

    def _send_child_page_response_list(self, page_response_list: list[PageResponse]) -> PageChildren:
        page_list = []
        for page_response in page_response_list:
            page = Page(self.namespace, page_response.id)
            page.last_response = page_response
            page_list.append(page)
        return PageChildren(page_list)

    def retrieve(self) -> DatabaseResponse:
        self.last_response = RetrieveDatabase(self.namespace.token, self.id).execute(self.namespace.print_body)
        return self.last_response

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: int = -1) -> Children[Page]:
        request = QueryDatabase(self.namespace.token, self.id, filter, sort, page_size)
        response_page_list = request.execute(self.namespace.print_body)
        return self._send_child_page_response_list(response_page_list)

    def update(self, title: RichText, properties: DatabaseProperties) -> DatabaseResponse:
        self.last_response = UpdateDatabase(self.namespace.token, self.id, title, properties).execute(
            self.namespace.print_body)
        return self.last_response

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.namespace.token, ParentInfo('database_id', self.id),
                                   properties, children, icon, cover).execute(self.namespace.print_body)
        page = Page(self.namespace, response_page.id)
        page.last_response = response_page
        return page


class Page(BaseBlock[PageResponse]):
    @property
    def parent(self) -> Union[Page, Block, None]:
        return self._get_parent(self.last_response.parent)

    def as_block(self) -> Block:
        block = Block(self.namespace, self.id)
        if self.last_response:
            block_response = BlockResponse(
                id=self.id,
                parent=self.last_response.parent,
                created_time=self.last_response.created_time,
                last_edited_time=self.last_response.last_edited_time,
                created_by=self.last_response.created_by,
                last_edited_by=self.last_response.last_edited_by,
                has_children=None,
                archived=self.last_response.archived,
                block_type=ChildPageBlockType(title=''),
            )
            block_response.timestamp = self.last_response.timestamp
            block.last_response = block_response
        return block

    def update(self, properties: Optional[PageProperties] = None, icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> PageResponse:
        self.last_response = UpdatePage(self.namespace.token, self.id, properties, icon, cover, archived).execute(
            self.namespace.print_body)
        return self.last_response

    def retrieve(self) -> PageResponse:
        self.last_response = RetrievePage(self.namespace.token, self.id).execute(self.namespace.print_body)
        return self.last_response

    def retrieve_property_item(self, prop_key: str | PropertyKey, page_size: int = -1) -> Any:
        # TODO: add type hint
        #  (concept) @overload (prop_id: PropertyKey[PagePropertyValue_T]) -> PagePropertyValue_T
        if isinstance(prop_key, PropertyKey):
            prop_key = prop_key.id
        page_property = RetrievePagePropertyItem(self.namespace.token, self.id, prop_key, page_size).execute(
            self.namespace.print_body)
        return page_property


Child_T = TypeVar('Child_T')


class Children(Sequence[Child_T]):
    def __init__(self, values: list[Child_T]):
        self._values: list[Child_T] = values
        self._by_id: dict[UUID, Child_T] = {child.id: child for child in self._values}

    def __getitem__(self, index_or_id: int | UUID) -> Child_T:
        if isinstance(index_or_id, int):
            return self._values[index_or_id]
        elif isinstance(index_or_id, UUID):
            return self._by_id[index_or_id]
        else:
            raise TypeError(f"Invalid argument type. Expected int or UUID - {index_or_id}")

    def get(self, index_or_id: int | UUID) -> Optional[Child_T]:
        try:
            return self[index_or_id]
        except (IndexError, KeyError):
            return None

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return f"{self.__class__.__name__}({repr(self._values)})"


BlockChildren = Children[Block]
PageChildren = Children[Page]
Namespace_KT = UUID | BaseBlock
Block_T = TypeVar('Block_T', bound=Block)
Database_T = TypeVar('Database_T', bound=Database)
Page_T = TypeVar('Page_T', bound=Page)


class Namespace(MutableMapping[Namespace_KT, BaseBlock_T]):
    # TODO: special type of blocks should be able to add their own keywords (for example, Block -> title)
    # TODO: add Settings
    def __init__(self, token: str = os.getenv('NOTION_TOKEN'), print_body: bool = False):
        self.token: Final = token
        self.print_body = print_body
        self.instances: dict[UUID, BaseBlock] = {}

    @staticmethod
    def _get_id(key: Namespace_KT) -> UUID:
        if isinstance(key, BaseBlock):
            return key.id
        if isinstance(key, UUID):
            return key
        raise NotionDfKeyError('bad id', {'key': key})

    def __getitem__(self, key: Namespace_KT) -> BaseBlock_T:
        return self.instances[self._get_id(key)]

    def __setitem__(self, key: Namespace_KT, value: BaseBlock_T) -> None:
        self.instances[self._get_id(key)] = value

    def __delitem__(self, key: Namespace_KT) -> None:
        del self.instances[self._get_id(key)]

    def __len__(self) -> int:
        return len(self.instances)

    def __iter__(self) -> Iterator[UUID]:
        return iter(self.instances)

    def block(self, id_or_url: UUID | str) -> Block:
        return Block(self, id_or_url)

    def database(self, id_or_url: UUID | str) -> Database:
        return Database(self, id_or_url)

    def page(self, id_or_url: UUID | str) -> Page:
        return Page(self, id_or_url)
