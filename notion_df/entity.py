from __future__ import annotations

from datetime import datetime
from typing import Optional, TypeVar, Union, Any, Literal, overload, Iterable
from uuid import UUID

from typing_extensions import Self

from notion_df.core.entity_base import Entity
from notion_df.core.exception import NotionDfValueError, NotionDfKeyError
from notion_df.core.request import Paginator
from notion_df.object.block import BlockValue, BlockResponse, ChildPageBlockValue, DatabaseResponse, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.partial_parent import PartialParent
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort, TimestampSort, Direction
from notion_df.object.user import PartialUser
from notion_df.property import Property, PageProperties, DatabaseProperties, PagePropertyValue_T
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.request.search import SearchByTitle
from notion_df.util.misc import repr_object, undefined
from notion_df.util.uuid_util import get_page_or_database_id, get_block_id
from notion_df.variable import Settings, token


class Block(Entity[BlockResponse]):
    parent: Union[Page, Block, None]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    has_children: Optional[bool]
    """the None value never occurs from direct server response. It only happens from Page.as_block()"""
    archived: bool
    value: BlockValue

    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_block_id(id_or_url)

    # noinspection DuplicatedCode
    def _send_response(self, response: BlockResponse) -> None:
        self.parent = response.parent
        self.created_time = response.created_time
        self.last_edited_time = response.last_edited_time
        self.created_by = response.created_by
        self.last_edited_by = response.last_edited_by
        self.has_children = response.has_children
        self.archived = response.archived
        self.value = response.value

    @staticmethod
    def _send_child_block_responses(block_responses: Iterable[BlockResponse]) -> Paginator[Block]:
        def it():
            for block_response in block_responses:
                block = Block(block_response.id)
                block.send_response(block_response)
                yield block

        return Paginator(Block, it())

    def retrieve(self) -> Self:
        response = RetrieveBlock(token, self.id).execute()
        return self.send_response(response)

    def retrieve_children(self) -> Paginator[Block]:
        block_responses = RetrieveBlockChildren(token, self.id).execute()
        return self._send_child_block_responses(block_responses)

    def update(self, block_type: Optional[BlockValue], archived: Optional[bool]) -> Self:
        response = UpdateBlock(token, self.id, block_type, archived).execute()
        return self.send_response(response)

    def delete(self) -> Self:
        response = DeleteBlock(token, self.id).execute()
        return self.send_response(response)

    def append_children(self, child_values: list[BlockValue]) -> list[Block]:
        if not child_values:
            return []
        block_responses = AppendBlockChildren(token, self.id, child_values).execute()
        return list(self._send_child_block_responses(block_responses))

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        database_response = CreateDatabase(token, self.id, title, properties, icon, cover).execute()
        database = Database(database_response.id)
        database.send_response(database_response)
        return database


class Database(Entity[DatabaseResponse]):
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

    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        try:
            title = self.title.plain_text
            url = self.url
            _id = undefined
        except (NotionDfKeyError, AttributeError):
            title = url = undefined
            _id = self.id
        return repr_object(self, title=title, url=url, id=_id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        try:
            title = self.title.plain_text
        except (NotionDfKeyError, AttributeError):
            title = undefined
        return repr_object(self, title=title)

    # noinspection DuplicatedCode
    def _send_response(self, response: DatabaseResponse) -> None:
        self.parent = response.parent
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
    def _send_child_page_responses(page_responses: Iterable[PageResponse]) -> Paginator[Page]:
        def it():
            for page_response in page_responses:
                page = Page(page_response.id)
                page.send_response(page_response)
                yield page

        return Paginator(Page, it())

    def retrieve(self) -> Self:
        if Settings.print and hasattr(self, 'title') and hasattr(self, 'url'):
            print('retrieve', self.title.plain_text, self.url)
        response = RetrieveDatabase(token, self.id).execute()
        return self.send_response(response)

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: Optional[int] = None) -> Paginator[Page]:
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


class Page(Entity[PageResponse]):
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

    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        try:
            title = self.properties.title.plain_text
            url = self.url
            _id = undefined
        except (NotionDfKeyError, AttributeError):
            title = url = undefined
            _id = self.id
        return repr_object(self, title=title, url=url, id=_id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        try:
            title = self.properties.title.plain_text
        except (NotionDfKeyError, AttributeError):
            title = undefined
        return repr_object(self, title=title)

    # noinspection DuplicatedCode
    def _send_response(self, response: PageResponse) -> None:
        self.parent = response.parent
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
        if self.last_timestamp > block.last_timestamp:
            block.parent = self.parent
            block.created_time = self.created_time
            block.last_edited_time = self.last_edited_time
            block.created_by = self.created_by
            block.last_edited_by = self.last_edited_by
            block.has_children = None
            block.archived = self.archived
            if not isinstance(getattr(block, 'value', None), ChildPageBlockValue):
                block.value = ChildPageBlockValue(title='')
            block.last_timestamp = self.last_timestamp
        return block

    def retrieve(self) -> Self:
        if Settings.print and hasattr(self, 'properties') and hasattr(self, 'url'):
            print('retrieve', self.properties.title.plain_text, self.url)
        response = RetrievePage(token, self.id).execute()
        return self.send_response(response)

    def retrieve_property_item(
            self, property_id: str | Property[Any, PagePropertyValue_T, Any]) -> PagePropertyValue_T:
        if isinstance(property_id, Property):
            property_id = property_id.id
            if property_id is None:
                raise NotionDfValueError(
                    "property.id is None. if you do not know the property id, retrieve the parent database first.",
                    {"self": self})
        page_property_value = RetrievePagePropertyItem(token, self.id, property_id).execute()
        if not hasattr(self, 'properties'):
            self.properties = PageProperties()
            self.properties[property_id] = page_property_value
        return page_property_value

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


Block_T = TypeVar('Block_T', bound=Block)
Database_T = TypeVar('Database_T', bound=Database)
Page_T = TypeVar('Page_T', bound=Page)


@overload
def search_by_title(query: str, entity: Literal['page'],
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> list[Page]:
    ...


@overload
def search_by_title(query: str, entity: Literal['database'],
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> list[Database]:
    ...


@overload
def search_by_title(query: str, entity: Literal[None],
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> list[Union[Page, Database]]:
    ...


def search_by_title(query: str, entity: Literal['page', 'database', None] = None,
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> Paginator[Union[Page, Database]]:
    response_elements = SearchByTitle(token, query, entity,
                                      TimestampSort('last_edited_time', sort_by_last_edited_time),
                                      page_size).execute()
    if entity == 'page':
        element_type = Page
    elif entity == 'database':
        element_type = Database
    else:
        element_type = Page | Database

    def it():
        for response_element in response_elements:
            if isinstance(response_element, DatabaseResponse):
                yield Database(response_element.id).send_response(response_element)
            elif isinstance(response_element, PageResponse):
                yield Page(response_element.id).send_response(response_element)
            else:
                raise NotionDfValueError('bad response', {'response_element': response_element})
        return

    return Paginator(element_type, it())
