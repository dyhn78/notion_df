from __future__ import annotations

import os
from abc import abstractmethod
from collections.abc import Sequence, MutableMapping
from datetime import datetime
from typing import Optional, TypeVar, Union, Generic, Iterator, final, Final

from typing_extensions import Self

from notion_df.object.block import BlockType, BlockResponse, ChildPageBlockType, DatabaseResponse, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.object.user import PartialUser
from notion_df.property import PropertyKey, PageProperties, DatabaseProperties, DatabasePropertyValue_T, \
    PagePropertyValue_T, FilterBuilder_T
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.request.request_core import Response_T
from notion_df.util.exception import NotionDfKeyError
from notion_df.util.misc import get_id, UUID


class BaseBlock(Generic[Response_T]):
    id: UUID
    timestamp: float
    parent: Union[Block, Database, Page, None]

    # noinspection PyShadowingBuiltins
    def __new__(cls, namespace: Namespace, id_or_url: Union[UUID, str]):
        id = get_id(id_or_url) if isinstance(id_or_url, str) else id_or_url
        if id in namespace:
            return namespace[id]
        __self = super().__new__(cls)
        namespace[id] = __self
        return __self

    def __init__(self, namespace: Namespace, id_or_url: Union[UUID, str]):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True
        self.namespace = namespace
        self.id = get_id(id_or_url)
        self.timestamp = 0

    @final
    def send_response(self, response: Response_T) -> bool:
        if response.timestamp > self.timestamp:
            self._send_response(response)
            return True
        return False

    @abstractmethod
    def _send_response(self, response: Response_T) -> None:
        pass

    @final
    def _get_parent(self, parent: ParentInfo) -> Union[Block, Database, Page, None]:
        if parent is None:
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
    parent: Union[Page, Block, None]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    has_children: Optional[bool]
    """the None value never occurs from direct server response. It only happens from Page.as_block()"""
    archived: bool
    block_type: BlockType

    def _send_response(self, response: BlockResponse) -> None:
        # noinspection DuplicatedCode
        self.parent = self._get_parent(response.parent)
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.created_by = response.created_by
        self.last_edited_by = response.last_edited_by
        self.has_children = response.has_children
        self.archived = response.archived
        self.block_type = response.block_type

    def _send_child_block_response_list(self, block_response_list: list[BlockResponse]) -> BlockChildren:
        block_list = []
        for block_response in block_response_list:
            block = Block(self.namespace, block_response.id)
            block.send_response(block_response)
            block_list.append(block)
        return BlockChildren(block_list)

    def retrieve(self) -> Self:
        response = RetrieveBlock(self.namespace.token, self.id).execute(self.namespace.print_body)
        self.send_response(response)
        return self

    def retrieve_children(self) -> BlockChildren:
        block_response_list = RetrieveBlockChildren(self.namespace.token, self.id).execute(self.namespace.print_body)
        return self._send_child_block_response_list(block_response_list)

    def update(self, block_type: Optional[BlockType], archived: Optional[bool]) -> Self:
        response = UpdateBlock(self.namespace.token, self.id, block_type, archived).execute(
            self.namespace.print_body)
        self.send_response(response)
        return self

    def delete(self) -> Self:
        response = DeleteBlock(self.namespace.token, self.id).execute(self.namespace.print_body)
        self.send_response(response)
        return self

    def append_children(self, block_type_list: list[BlockType]) -> BlockChildren:
        block_response_list = AppendBlockChildren(self.namespace.token, self.id, block_type_list).execute(
            self.namespace.print_body)
        return self._send_child_block_response_list(block_response_list)

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        page_response = CreatePage(self.namespace.token, ParentInfo('page_id', self.id),
                                   properties, children, icon, cover).execute(self.namespace.print_body)
        page = Page(self.namespace, page_response.id)
        page.send_response(page_response)
        return page

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        database_response = CreateDatabase(self.namespace.token, self.id, title, properties, icon, cover).execute(
            self.namespace.print_body)
        database = Database(self.namespace, database_response.id)
        database.send_response(database_response)
        return database


class Database(BaseBlock[DatabaseResponse]):
    parent: Union[Page, Block, None]
    created_time: datetime
    last_edited_time: datetime
    icon: Optional[Icon]
    cover: Optional[ExternalFile]
    url: str
    title: RichText
    properties: DatabaseProperties
    archived: bool
    is_inline: bool

    def _send_response(self, response: DatabaseResponse) -> None:
        # noinspection DuplicatedCode
        self.parent = self._get_parent(response.parent)
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.icon = response.icon
        self.cover = response.cover
        self.url = response.url
        self.title = response.title
        self.properties = response.properties
        self.archived = response.archived
        self.is_inline = response.is_inline

    def _send_child_page_response_list(self, page_response_list: list[PageResponse]) -> PageChildren:
        page_list = []
        for page_response in page_response_list:
            page = Page(self.namespace, page_response.id)
            page.send_response(page_response)
            page_list.append(page)
        return PageChildren(page_list)

    def retrieve(self) -> Self:
        response = RetrieveDatabase(self.namespace.token, self.id).execute(self.namespace.print_body)
        self.send_response(response)
        return self

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: int = -1) -> Children[Page]:
        request = QueryDatabase(self.namespace.token, self.id, filter, sort, page_size)
        page_response_list = request.execute(self.namespace.print_body)
        return self._send_child_page_response_list(page_response_list)

    def update(self, title: RichText, properties: DatabaseProperties) -> Self:
        response = UpdateDatabase(self.namespace.token, self.id, title, properties).execute(self.namespace.print_body)
        self.send_response(response)
        return self

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.namespace.token, ParentInfo('database_id', self.id),
                                   properties, children, icon, cover).execute(self.namespace.print_body)
        page = Page(self.namespace, response_page.id)
        page.send_response(response_page)
        return page


class Page(BaseBlock[PageResponse]):
    parent: Union[Page, Block, Database, None]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    archived: bool
    icon: Optional[Icon]
    cover: Optional[ExternalFile]
    url: str
    properties: PageProperties

    def _send_response(self, response: PageResponse) -> None:
        # noinspection DuplicatedCode
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.created_by = response.created_by
        self.last_edited_by = response.last_edited_by
        self.archived = response.archived
        self.icon = response.icon
        self.cover = response.cover
        self.url = response.url
        self.properties = response.properties

    def as_block(self) -> Block:
        block = Block(self.namespace, self.id)
        if self.timestamp > block.timestamp:
            block.parent = self.parent
            block.created_time = self.created_time
            block.last_edited_time = self.last_edited_time
            block.created_by = self.created_by
            block.last_edited_by = self.last_edited_by
            block.has_children = None
            block.archived = self.archived
            if not isinstance(getattr(block, 'block_type', None), ChildPageBlockType):
                block.block_type = ChildPageBlockType(title='')
            block.timestamp = self.timestamp
        return block

    def update(self, properties: Optional[PageProperties] = None, icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> Self:
        response = UpdatePage(self.namespace.token, self.id, properties, icon, cover, archived).execute(
            self.namespace.print_body)
        self.send_response(response)
        return self

    def retrieve(self) -> Self:
        response = RetrievePage(self.namespace.token, self.id).execute(self.namespace.print_body)
        self.send_response(response)
        return self

    def retrieve_property_item(
            self, prop_key: str | PropertyKey[DatabasePropertyValue_T, PagePropertyValue_T, FilterBuilder_T],
            page_size: int = -1) -> PagePropertyValue_T:
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
        self._values: dict[UUID, BaseBlock] = {}

    @staticmethod
    def _get_id(key: Namespace_KT) -> UUID:
        if isinstance(key, BaseBlock):
            return key.id
        if isinstance(key, UUID):
            return key
        raise NotionDfKeyError('bad id', {'key': key})

    def __getitem__(self, key: Namespace_KT) -> BaseBlock_T:
        return self._values[self._get_id(key)]

    def __setitem__(self, key: Namespace_KT, value: BaseBlock_T) -> None:
        self._values[self._get_id(key)] = value

    def __delitem__(self, key: Namespace_KT) -> None:
        del self._values[self._get_id(key)]

    def __len__(self) -> int:
        return len(self._values)

    def __iter__(self) -> Iterator[UUID]:
        return iter(self._values)

    def block(self, id_or_url: UUID | str) -> Block:
        return Block(self, id_or_url)

    def database(self, id_or_url: UUID | str) -> Database:
        return Database(self, id_or_url)

    def page(self, id_or_url: UUID | str) -> Page:
        return Page(self, id_or_url)
