from __future__ import annotations

import os
from abc import abstractmethod
from collections.abc import Sequence
from datetime import datetime
from functools import cache
from typing import Optional, TypeVar, Union, Generic, final, Final

from typing_extensions import Self

from notion_df.object.block import BlockValue, BlockResponse, ChildPageBlockValue, DatabaseResponse, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.object.user import PartialUser
from notion_df.property import Property, PageProperties, DatabaseProperties, DatabasePropertyValue_T, \
    PagePropertyValue_T, FilterBuilder_T
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.request.request_core import Response_T
from notion_df.util.exception import NotionDfTypeError, NotionDfValueError
from notion_df.util.misc import get_id, UUID, repr_object
from notion_df.variable import Settings

token: Final[str] = os.getenv('NOTION_TOKEN')  # TODO: support multiple token


class BaseBlock(Generic[Response_T]):
    id: UUID
    timestamp: float
    parent: Union[Block, Database, Page, None]

    def __new__(cls, id_or_url: Union[UUID, str], namespace: Namespace = None):
        if namespace is None:
            namespace = default_namespace
        _id = get_id(id_or_url)
        if (cls, _id) in namespace:
            return namespace[(cls, _id)]
        return super().__new__(cls)

    def __init__(self, id_or_url: Union[UUID, str], namespace: Namespace = None):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.id: Final[UUID] = get_id(id_or_url)
        if namespace is None:
            namespace = default_namespace
        self.namespace = namespace
        self.namespace[(type(self), self.id)] = self
        self.timestamp = 0

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def __eq__(self, other: BaseBlock) -> bool:
        return type(self) == type(other) and self.id == other.id

    @cache
    def __repr__(self) -> str:
        return repr_object(self, {'id': str(self.id), 'parent': repr_object(self.parent, {'id': str(self.id)})})

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
                return Block(parent.id, self.namespace)
            case 'database_id':
                return Database(parent.id, self.namespace)
            case 'page_id':
                return Page(parent.id, self.namespace)
            case 'workspace':
                return None


Namespace = dict[tuple[type[BaseBlock], UUID], BaseBlock]
default_namespace: Final[Namespace] = {}


class Block(BaseBlock[BlockResponse]):
    parent: Union[Page, Block, None]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    has_children: Optional[bool]
    """the None value never occurs from direct server response. It only happens from Page.as_block()"""
    archived: bool
    value: BlockValue

    def _send_response(self, response: BlockResponse) -> None:
        # noinspection DuplicatedCode
        self.parent = self._get_parent(response.parent)
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.created_by = response.created_by
        self.last_edited_by = response.last_edited_by
        self.has_children = response.has_children
        self.archived = response.archived
        self.value = response.value

    def _send_child_block_response_list(self, block_response_list: list[BlockResponse]) -> BlockChildren:
        block_list = []
        for block_response in block_response_list:
            block = Block(block_response.id, self.namespace)
            block.send_response(block_response)
            block_list.append(block)
        return BlockChildren(block_list)

    def retrieve(self) -> Self:
        response = RetrieveBlock(token, self.id).execute()
        self.send_response(response)
        return self

    def retrieve_children(self) -> BlockChildren:
        block_response_list = RetrieveBlockChildren(token, self.id).execute()
        return self._send_child_block_response_list(block_response_list)

    def update(self, block_type: Optional[BlockValue], archived: Optional[bool]) -> Self:
        response = UpdateBlock(token, self.id, block_type, archived).execute()
        self.send_response(response)
        return self

    def delete(self) -> Self:
        response = DeleteBlock(token, self.id).execute()
        self.send_response(response)
        return self

    def append_children(self, child_values: list[BlockValue]) -> BlockChildren:
        block_response_list = AppendBlockChildren(token, self.id, child_values).execute()
        return self._send_child_block_response_list(block_response_list)

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        database_response = CreateDatabase(token, self.id, title, properties, icon, cover).execute()
        database = Database(database_response.id)
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
            page = Page(page_response.id, self.namespace)
            page.send_response(page_response)
            page_list.append(page)
        return PageChildren(page_list)

    def retrieve(self) -> Self:
        response = RetrieveDatabase(token, self.id).execute()
        self.send_response(response)
        return self

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: int = -1) -> Children[Page]:
        if Settings.print_body:
            print('query', self.title.plain_text, self.url)
        request = QueryDatabase(token, self.id, filter, sort, page_size)
        page_response_list = request.execute()
        return self._send_child_page_response_list(page_response_list)

    def update(self, title: RichText, properties: DatabaseProperties) -> Self:
        if Settings.print_body:
            print('update', self.title.plain_text, self.url)
        response = UpdateDatabase(token, self.id, title, properties).execute()
        self.send_response(response)
        return self

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        if Settings.print_body:
            print('create_child_page', self.title.plain_text, self.url)
        response_page = CreatePage(token, ParentInfo('database_id', self.id),
                                   properties, children, icon, cover).execute()
        page = Page(response_page.id)
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
        block = Block(self.id, self.namespace)
        if self.timestamp > block.timestamp:
            block.parent = self.parent
            block.created_time = self.created_time
            block.last_edited_time = self.last_edited_time
            block.created_by = self.created_by
            block.last_edited_by = self.last_edited_by
            block.has_children = None
            block.archived = self.archived
            if not isinstance(getattr(block, 'value', None), ChildPageBlockValue):
                block.value = ChildPageBlockValue(title='')
            block.timestamp = self.timestamp
        return block

    def update(self, properties: Optional[PageProperties] = None, icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> Self:
        if Settings.print_body:
            print('update', self.properties.title.plain_text, self.url)
        response = UpdatePage(token, self.id, properties, icon, cover, archived).execute()
        self.send_response(response)
        return self

    def retrieve(self) -> Self:
        response = RetrievePage(token, self.id).execute()
        self.send_response(response)
        return self

    def retrieve_property_item(
            self, property_id: str | Property[DatabasePropertyValue_T, PagePropertyValue_T, FilterBuilder_T],
            page_size: int = -1) -> PagePropertyValue_T:
        if isinstance(property_id, Property):
            property_id = property_id.id
        if property_id is None:
            raise NotionDfValueError('property_id is None', {'self': self})
        page_property = RetrievePagePropertyItem(token, self.id, property_id, page_size).execute()
        return page_property

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        if Settings.print_body:
            print('create_child_page', self.properties.title.plain_text, self.url)
        page_response = CreatePage(token, ParentInfo('page_id', self.id),
                                   properties, children, icon, cover).execute()
        page = Page(page_response.id)
        page.send_response(page_response)
        return page

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        if Settings.print_body:
            print('create_child_database', self.properties.title.plain_text, self.url)
        return self.as_block().create_child_database(title, properties=properties, icon=icon, cover=cover)


Child_T = TypeVar('Child_T')


class Children(Sequence[Child_T]):
    def __init__(self, values: list[Child_T]):
        self._values: list[Child_T] = values
        self._by_id: dict[UUID, Child_T] = {child.id: child for child in self._values}

    def __getitem__(self, index_or_id: int | UUID | slice) -> Child_T:
        if isinstance(index_or_id, int) or isinstance(index_or_id, slice):
            return self._values[index_or_id]
        elif isinstance(index_or_id, UUID):
            return self._by_id[index_or_id]
        else:
            raise NotionDfTypeError("Invalid argument type. Expected int, UUID or slice", {'index_or_id': index_or_id})

    def get(self, index_or_id: int | UUID | slice) -> Optional[Child_T]:
        try:
            return self[index_or_id]
        except (IndexError, KeyError):
            return None

    def __len__(self):
        return len(self._values)

    def __repr__(self):
        return repr_object(self, ['values'])


BlockChildren = Children[Block]
PageChildren = Children[Page]
Namespace_KT = UUID | BaseBlock
Block_T = TypeVar('Block_T', bound=Block)
Database_T = TypeVar('Database_T', bound=Database)
Page_T = TypeVar('Page_T', bound=Page)
