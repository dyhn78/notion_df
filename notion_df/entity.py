from __future__ import annotations

from typing import Optional, TypeVar, Union, Any, Literal, overload, Iterable
from uuid import UUID

from notion_df.core.entity_core import Entity
from notion_df.core.exception import NotionDfValueError, NotionDfKeyError
from notion_df.core.request import Paginator
from notion_df.data.common import Icon
from notion_df.data.entity_data import BlockValue, BlockData, ChildPageBlockValue, DatabaseData, PageData
from notion_df.data.file import ExternalFile, File
from notion_df.data.filter import Filter
from notion_df.data.partial_parent import PartialParent
from notion_df.data.rich_text import RichText
from notion_df.data.sort import Sort, TimestampSort, Direction
from notion_df.property import Property, PageProperties, DatabaseProperties, PagePropertyValue_T
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.request.search import SearchByTitle
from notion_df.util.misc import repr_object, undefined
from notion_df.util.uuid_util import get_page_or_database_id, get_block_id
from notion_df.variable import Settings, token


class Block(Entity[BlockData]):
    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_block_id(id_or_url)

    @staticmethod
    def _send_child_block_datas(block_datas: Iterable[BlockData]) -> Paginator[Block]:
        def it():
            for block_data in block_datas:
                block = Block(block_data.id)
                block.set_data(block_data)
                yield block

        return Paginator(Block, it())

    def retrieve(self) -> BlockData:
        return self.set_data(RetrieveBlock(token, self.id).execute())

    def retrieve_children(self) -> Paginator[Block]:
        block_datas = RetrieveBlockChildren(token, self.id).execute()
        return self._send_child_block_datas(block_datas)

    def update(self, block_type: Optional[BlockValue], archived: Optional[bool]) -> BlockData:
        return self.set_data(UpdateBlock(token, self.id, block_type, archived).execute())

    def delete(self) -> BlockData:
        return self.set_data(DeleteBlock(token, self.id).execute())

    def append_children(self, child_values: list[BlockValue]) -> list[Block]:
        if not child_values:
            return []
        block_datas = AppendBlockChildren(token, self.id, child_values).execute()
        return list(self._send_child_block_datas(block_datas))

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        data = CreateDatabase(token, self.id, title, properties, icon, cover).execute()
        db = Database(data.id)
        db.set_data(data)
        return db


class Database(Entity[DatabaseData]):
    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        try:
            title = self.data.title.plain_text
            url = self.data.url
            return repr_object(self, title=title, url=url, parent=self._repr_parent())
        except (NotionDfKeyError, AttributeError):
            return repr_object(self, id=self.id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        try:
            title = self.data.title.plain_text
            return repr_object(self, title=title)
        except (NotionDfKeyError, AttributeError):
            return repr_object(self, id=self.id)

    @staticmethod
    def _send_child_page_datas(page_datas: Iterable[PageData]) -> Paginator[Page]:
        def it():
            for page_data in page_datas:
                page = Page(page_data.id)
                page.set_data(page_data)
                yield page

        return Paginator(Page, it())

    def retrieve(self) -> DatabaseData:
        if Settings.print and self.data:
            print('retrieve', self.data.title.plain_text, self.data.url)
        return self.set_data(RetrieveDatabase(token, self.id).execute())

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: Optional[int] = None) -> Paginator[Page]:
        if Settings.print and self.data:
            print('query', self.data.title.plain_text, self.data.url)
        page_datas = QueryDatabase(token, self.id, filter, sort, page_size).execute()
        return self._send_child_page_datas(page_datas)

    def update(self, title: RichText, properties: DatabaseProperties) -> DatabaseData:
        if Settings.print and self.data:
            print('update', self.data.title.plain_text, self.data.url)
        return self.set_data(UpdateDatabase(token, self.id, title, properties).execute())

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        if Settings.print and self.data:
            print('create_child_page', self.data.title.plain_text, self.data.url)
        page_data = CreatePage(token, PartialParent('database_id', self.id),
                               properties, children, icon, cover).execute()
        page = Page(page_data.id)
        page.set_data(page_data)
        return page


class Page(Entity[PageData]):
    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        try:
            title = self.data.properties.title.plain_text
            url = self.data.url
            _id = undefined
        except (NotionDfKeyError, AttributeError):
            title = url = undefined
            _id = self.id
        return repr_object(self, title=title, url=url, id=_id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        try:
            title = self.data.properties.title.plain_text
            return repr_object(self, title=title)
        except (NotionDfKeyError, AttributeError):
            return repr_object(self, id=self.id)

    def as_block(self) -> Block:
        block = Block(self.id)
        if block.data is None or self.data.timestamp > block.data.timestamp:
            block.set_data(BlockData(id=self.id,
                                     parent=self.data.parent,
                                     created_time=self.data.created_time,
                                     last_edited_time=self.data.last_edited_time,
                                     created_by=self.data.created_by,
                                     last_edited_by=self.data.last_edited_by,
                                     has_children=(block.data.has_children if block.data else None),
                                     archived=self.data.archived,
                                     value=(block.data.value if block.data else ChildPageBlockValue(title=''))))
            block.data.timestamp = self.data.timestamp
        return block

    def retrieve(self) -> PageData:
        if Settings.print and self.data:
            print('retrieve', self.data.properties.title.plain_text, self.data.url)
        return self.set_data(RetrievePage(token, self.id).execute())

    def retrieve_property_item(
            self, property_id: str | Property[Any, PagePropertyValue_T, Any]) -> PagePropertyValue_T:
        if isinstance(prop := property_id, Property):
            property_id = prop.id
            if property_id is None:
                raise NotionDfValueError(
                    "property.id is None. if you do not know the property id, retrieve the parent database first.",
                    {"self": self})
            _, prop_value = RetrievePagePropertyItem(token, self.id, property_id).execute()
        else:
            prop, prop_value = RetrievePagePropertyItem(token, self.id, property_id).execute()
        if self.data:
            self.data.properties[prop] = prop_value
        return prop_value

    def update(self, properties: Optional[PageProperties] = None, icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> PageData:
        if Settings.print and self.data:
            print('update', self.data.properties.title.plain_text, self.data.url)
        return self.set_data(UpdatePage(token, self.id, properties, icon, cover, archived).execute())

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        if Settings.print:
            print('create_child_page', self.data.properties.title.plain_text, self.data.url)
        page_data = CreatePage(token, PartialParent('page_id', self.id), properties, children, icon, cover).execute()
        page = Page(page_data.id)
        page.set_data(page_data)
        return page

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        if Settings.print:
            print('create_child_database', self.data.properties.title.plain_text, self.data.url)
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
    data_elements = SearchByTitle(token, query, entity,
                                  TimestampSort('last_edited_time', sort_by_last_edited_time),
                                  page_size).execute()
    if entity == 'page':
        element_type = Page
    elif entity == 'database':
        element_type = Database
    else:
        element_type = Page | Database

    def it():
        for data_element in data_elements:
            if isinstance(data_element, DatabaseData):
                db = Database(data_element.id)
                db.set_data(data_element)
                yield db
            elif isinstance(data_element, PageData):
                page = Page(data_element.id)
                page.set_data(data_element)
                yield page
            else:
                raise NotionDfValueError('bad data', {'data_element': data_element})
        return

    it()

    return Paginator(element_type, it())
