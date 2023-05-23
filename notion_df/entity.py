from __future__ import annotations

import os
from abc import abstractmethod
from collections.abc import Sequence
from datetime import datetime
from functools import cache
from typing import Optional, TypeVar, Union, Generic, final, Final, Any, Literal, overload, Hashable, Iterator, Iterable

from typing_extensions import Self

from notion_df.object.block import BlockValue, BlockResponse, ChildPageBlockValue, DatabaseResponse, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.parent import PartialParent
from notion_df.object.property import Property, PageProperties, DatabaseProperties, PagePropertyValue_T
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort, TimestampSort, Direction
from notion_df.object.user import PartialUser
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.request.request_core import Response_T
from notion_df.request.search import SearchByTitle
from notion_df.util.exception import NotionDfTypeError, NotionDfValueError, NotionDfKeyError
from notion_df.util.misc import get_id, UUID, repr_object
from notion_df.variable import Settings

token: Final[str] = os.getenv('NOTION_TOKEN')  # TODO: support multiple token
namespace: Final[dict[tuple[type[BaseBlock], UUID], BaseBlock]] = {}


class BaseBlock(Generic[Response_T], Hashable):
    """The base block class.
    There is only one block instance with given subclass and id.
    You can compare two blocks directly `block_1 == block_2`, not having to compare id `block_1.id == block_2.id`"""
    id: UUID
    timestamp: float
    parent: Union[Block, Database, Page, None]

    def __new__(cls, id_or_url: Union[UUID, str]):
        _id = get_id(id_or_url)
        if (cls, _id) in namespace:
            return namespace[(cls, _id)]
        return super().__new__(cls)

    def __init__(self, id_or_url: Union[UUID, str]):
        if hasattr(self, '_initialized'):
            return
        self._initialized = True

        self.id: Final[UUID] = get_id(id_or_url)
        namespace[(type(self), self.id)] = self
        self.timestamp = 0

    def __hash__(self) -> int:
        return hash((type(self), self.id))

    def __eq__(self, other: BaseBlock) -> bool:
        return type(self) == type(other) and self.id == other.id

    @final
    @cache
    def __repr__(self) -> str:
        if not hasattr(self, 'parent'):
            repr_parent = None
        elif self.parent is None:
            repr_parent = 'workspace'
        else:
            repr_parent = repr_object(self.parent, self.parent._attrs_to_repr_parent())

        return repr_object(self, {
            **self._attrs_to_repr_parent(),
            'id_or_url': getattr(self, 'url', str(self.id)),
            'parent': repr_parent
        })

    def _attrs_to_repr_parent(self) -> dict[str, Any]:
        return {}

    @final
    def send_response(self, response: Response_T) -> Self:
        if response.timestamp > self.timestamp:
            self._send_response(response)
        return self

    @abstractmethod
    def _send_response(self, response: Response_T) -> None:
        pass


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

    # noinspection DuplicatedCode
    def _send_response(self, response: BlockResponse) -> None:
        self.parent = response.parent.entity
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.created_by = response.created_by
        self.last_edited_by = response.last_edited_by
        self.has_children = response.has_children
        self.archived = response.archived
        self.value = response.value

    @staticmethod
    def _send_child_block_responses(block_responses: Iterable[BlockResponse]) -> Children[Block]:
        block_list = []
        for block_response in block_responses:
            block = Block(block_response.id)
            block.send_response(block_response)
            block_list.append(block)
        return Children(block_list)

    def retrieve(self) -> Self:
        response = RetrieveBlock(token, self.id).execute()
        return self.send_response(response)

    def retrieve_children(self) -> Children[Block]:
        block_responses = RetrieveBlockChildren(token, self.id).execute()
        return self._send_child_block_responses(block_responses)

    def update(self, block_type: Optional[BlockValue], archived: Optional[bool]) -> Self:
        response = UpdateBlock(token, self.id, block_type, archived).execute()
        return self.send_response(response)

    def delete(self) -> Self:
        response = DeleteBlock(token, self.id).execute()
        return self.send_response(response)

    def append_children(self, child_values: list[BlockValue]) -> Children[Block]:
        if not child_values:
            return Children([])
        block_responses = AppendBlockChildren(token, self.id, child_values).execute()
        return self._send_child_block_responses(block_responses)

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

    def _attrs_to_repr_parent(self) -> dict[str, Any]:
        try:
            title_value = self.title.plain_text
        except AttributeError:
            title_value = None
        return {
            'title': title_value,
        }

    # noinspection DuplicatedCode
    def _send_response(self, response: DatabaseResponse) -> None:
        self.parent = response.parent.entity
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.icon = response.icon
        self.cover = response.cover
        self.url = response.url
        self.title = response.title
        self.properties = response.properties
        self.archived = response.archived
        self.is_inline = response.is_inline

    @staticmethod
    def _send_child_page_responses(page_responses: Iterable[PageResponse]) -> Children[Page]:
        page_list = []
        for page_response in page_responses:
            page = Page(page_response.id)
            page.send_response(page_response)
            page_list.append(page)
        return Children(page_list)

    def retrieve(self) -> Self:
        if Settings.print and hasattr(self, 'title') and hasattr(self, 'url'):
            print('retrieve', self.title.plain_text, self.url)
        response = RetrieveDatabase(token, self.id).execute()
        return self.send_response(response)

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: Optional[int] = None) -> Children[Page]:
        if Settings.print and hasattr(self, 'title') and hasattr(self, 'url'):
            print('query', self.title.plain_text, self.url)
        page_responses = QueryDatabase(token, self.id, filter, sort, page_size).execute()
        return self._send_child_page_responses(page_responses)

    def update(self, title: RichText, properties: DatabaseProperties) -> Self:
        if Settings.print and hasattr(self, 'title') and hasattr(self, 'url'):
            print('update', self.title.plain_text, self.url)
        response = UpdateDatabase(token, self.id, title, properties).execute()
        return self.send_response(response)

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        if Settings.print and hasattr(self, 'title') and hasattr(self, 'url'):
            print('create_child_page', self.title.plain_text, self.url)
        response_page = CreatePage(token, PartialParent('database_id', self.id),
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

    def _attrs_to_repr_parent(self) -> dict[str, Any]:
        try:
            title_value = self.properties.title.plain_text
        except (NotionDfKeyError, AttributeError):
            title_value = None
        return {
            'title': title_value,
        }

    # noinspection DuplicatedCode
    def _send_response(self, response: PageResponse) -> None:
        self.parent = response.parent.entity
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
        block = Block(self.id)
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

    def retrieve(self) -> Self:
        if Settings.print and hasattr(self, 'properties') and hasattr(self, 'url'):
            print('retrieve', self.properties.title.plain_text, self.url)
        response = RetrievePage(token, self.id).execute()
        return self.send_response(response)

    def retrieve_property_item(self, property_id: str | Property[Any, PagePropertyValue_T, Any],
                               page_size: Optional[int] = None) -> PagePropertyValue_T:
        if isinstance(property_id, Property):
            property_id = property_id.id
        if property_id is None:
            raise NotionDfValueError('property_id is None', {'self': self})
        page_property = RetrievePagePropertyItem(token, self.id, property_id, page_size).execute()
        return page_property

    def update(self, properties: Optional[PageProperties] = None, icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> Self:
        if Settings.print and hasattr(self, 'properties') and hasattr(self, 'url'):
            print('update', self.properties.title.plain_text, self.url)
        response = UpdatePage(token, self.id, properties, icon, cover, archived).execute()
        return self.send_response(response)

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        if Settings.print:
            print('create_child_page', self.properties.title.plain_text, self.url)
        page_response = CreatePage(token, PartialParent('page_id', self.id),
                                   properties, children, icon, cover).execute()
        page = Page(page_response.id)
        page.send_response(page_response)
        return page

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        if Settings.print:
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


Namespace_KT = UUID | BaseBlock
Block_T = TypeVar('Block_T', bound=Block)
Database_T = TypeVar('Database_T', bound=Database)
Page_T = TypeVar('Page_T', bound=Page)


@overload
def search_by_title(query: str, entity: Literal['page'],
                    sort: TimestampSort = TimestampSort('last_edited_time', 'descending'),
                    page_size: int = None) -> list[Page]:
    ...


@overload
def search_by_title(query: str, entity: Literal['database'],
                    sort: TimestampSort = TimestampSort('last_edited_time', 'descending'),
                    page_size: int = None) -> list[Database]:
    ...


@overload
def search_by_title(query: str, entity: Literal[None],
                    sort: TimestampSort = TimestampSort('last_edited_time', 'descending'),
                    page_size: int = None) -> list[Union[Page, Database]]:
    ...


def search_by_title(query: str, entity: Literal['page', 'database', None] = None,
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> Iterator[Union[Page, Database]]:
    response_elements = SearchByTitle(token, query, entity,
                                      TimestampSort('last_edited_time', sort_by_last_edited_time),
                                      page_size).execute()
    for response_element in response_elements:
        if isinstance(response_element, DatabaseResponse):
            yield Database(response_element.id).send_response(response_element)
        elif isinstance(response_element, PageResponse):
            yield Page(response_element.id).send_response(response_element)
        else:
            raise NotionDfValueError('bad response', {'response_element': response_element})
    return
