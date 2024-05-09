from __future__ import annotations

from datetime import datetime
from typing import Optional, TypeVar, Union, Any, Literal, overload, Iterable
from uuid import UUID

from loguru import logger
from typing_extensions import Self

from notion_df.core.entity import RetrievableEntity
from notion_df.core.exception import NotionDfValueError, NotionDfKeyError
from notion_df.core.request import Paginator
from notion_df.object.data import BlockValue, BlockData, ChildPageBlockValue, \
    DatabaseData, PageData
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.misc import Icon, PartialParent
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort, TimestampSort, Direction
from notion_df.object.user import PartialUser
from notion_df.property import Property, PageProperties, DatabaseProperties, \
    PagePropertyValueT
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, \
    RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, \
    QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, \
    RetrievePagePropertyItem
from notion_df.request.search import SearchByTitle
from notion_df.util.misc import repr_object, undefined
from notion_df.util.uuid_util import get_page_or_database_id, get_block_id
from notion_df.variable import token


class Block(RetrievableEntity[BlockData]):
    data_cls = BlockData

    @property
    def parent(self) -> Union[Block, Page, None]:
        return self.data.parent

    @property
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    def created_by(self) -> PartialUser:
        return self.data.created_by

    @property
    def last_edited_by(self) -> PartialUser:
        return self.data.last_edited_by

    @property
    def has_children(self) -> Optional[bool]:
        """Note: the None value never occurs from direct server data. It only happens from Page.as_block()"""
        return self.data.has_children

    @property
    def archived(self) -> bool:
        return self.data.archived

    @property
    def value(self) -> BlockValue:
        return self.data.value

    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_block_id(id_or_url)

    @staticmethod
    def _send_child_block_datas(block_datas: Iterable[BlockData]) -> Paginator[Block]:
        def it():
            for block_data in block_datas:
                yield Block(block_data.id)

        return Paginator(Block, it())

    def retrieve(self) -> Self:
        logger.info(f'Block.retrieve({self})')
        RetrieveBlock(token, self.id).execute()
        return self

    def retrieve_children(self) -> Paginator[Block]:
        logger.info(f'Block.retrieve_children({self})')
        block_datas = RetrieveBlockChildren(token, self.id).execute()
        return self._send_child_block_datas(block_datas)

    def update(self, block_type: Optional[BlockValue], archived: Optional[bool]) -> Self:
        logger.info(f'Block.update({self})')
        UpdateBlock(token, self.id, block_type, archived).execute()
        return self

    def delete(self) -> Self:
        logger.info(f'Block.delete({self})')
        DeleteBlock(token, self.id).execute()
        return self

    def append_children(self, child_values: list[BlockValue]) -> list[Block]:
        logger.info(f'Block.append_children({self})')
        if not child_values:
            return []
        block_datas = AppendBlockChildren(token, self.id, child_values).execute()
        return list(self._send_child_block_datas(block_datas))

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        logger.info(f'Block.create_child_database({self})')
        data = CreateDatabase(token, self.id, title, properties, icon,
                                  cover).execute()
        return Database(data.id)


class Database(RetrievableEntity[DatabaseData]):
    data_cls = DatabaseData

    @property
    def parent(self) -> Union[Block, Page, None]:
        return self.data.parent

    @property
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    def icon(self) -> Optional[Icon]:
        return self.data.icon

    @property
    def cover(self) -> Optional[File]:
        return self.data.cover

    @property
    def url(self) -> str:
        return self.data.url

    @property
    def title(self) -> RichText:
        return self.data.title

    @property
    def properties(self) -> DatabaseProperties:
        return self.data.properties

    @property
    def archived(self) -> bool:
        return self.data.archived

    @property
    def is_inline(self) -> bool:
        return self.data.is_inline

    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        try:
            if not self.data:
                raise AttributeError
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
    def _send_child_page_data(page_data_it: Iterable[PageData]) -> Paginator[Page]:
        def it():
            for page_data in page_data_it:
                yield Page(page_data.id)

        return Paginator(Page, it())

    def retrieve(self) -> Self:
        logger.info(f'Database.retrieve({self})')
        RetrieveDatabase(token, self.id).execute()
        return self

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: Optional[int] = None) -> Paginator[Page]:
        logger.info(f'Database.query({self})')
        page_data = QueryDatabase(token, self.id, filter, sort, page_size).execute()
        return self._send_child_page_data(page_data)

    def update(self, title: RichText, properties: DatabaseProperties) -> Database:
        logger.info(f'Database.update({self})')
        UpdateDatabase(token, self.id, title, properties).execute()
        return self

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        logger.info(f'Database.create_child_page({self})')
        page_data = CreatePage(token, PartialParent('database_id', self.id),
                               properties, children, icon, cover).execute()
        return Page(page_data.id)


class Page(RetrievableEntity[PageData]):
    data_cls = PageData

    @property
    def parent(self) -> Union[Block, Database, Page, None]:
        return self.data.parent

    @property
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    def created_by(self) -> PartialUser:
        return self.data.created_by

    @property
    def last_edited_by(self) -> PartialUser:
        return self.data.last_edited_by

    @property
    def icon(self) -> Optional[Icon]:
        return self.data.icon

    @property
    def cover(self) -> Optional[File]:
        return self.data.cover

    @property
    def url(self) -> str:
        return self.data.url

    @property
    def archived(self) -> bool:
        return self.data.archived

    @property
    def properties(self) -> PageProperties:
        return self.data.properties

    @classmethod
    def _get_id(cls, id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        try:
            if not self.data:
                raise AttributeError
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
        latest = BlockData(id=self.id,
                           parent=self.data.parent,
                           created_time=self.data.created_time,
                           last_edited_time=self.data.last_edited_time,
                           created_by=self.data.created_by,
                           last_edited_by=self.data.last_edited_by,
                           has_children=(
                               block.data.has_children if block.data else None),
                           archived=self.data.archived,
                           value=(
                               block.data.value if block.data
                               else ChildPageBlockValue(title='')))
        latest.timestamp = self.data.timestamp
        return block

    def retrieve(self) -> Self:
        logger.info(f'Page.retrieve({self})')
        RetrievePage(token, self.id).execute()
        return self

    def retrieve_property_item(
            self, property_id: str | Property[Any, PagePropertyValueT, Any]) -> PagePropertyValueT:
        logger.info(f'Page.retrieve_property_item({self}, property_id="{property_id}")')
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
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> Self:
        logger.info(f'Page.update({self})')
        UpdatePage(token, self.id, properties, icon, cover, archived).execute()
        return self

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        logger.info(f'Page.create_child_page({self})')
        page_data = CreatePage(token, PartialParent('page_id', self.id), properties, children, icon, cover).execute()
        return Page(page_data.id)

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        logger.info(f'Page.create_child_database({self})')
        return self.as_block().create_child_database(title, properties=properties, icon=icon, cover=cover)


BlockT = TypeVar('BlockT', bound=Block)
DatabaseT = TypeVar('DatabaseT', bound=Database)
PageT = TypeVar('PageT', bound=Page)


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
    contents_it = SearchByTitle(
        token, query, entity,
        TimestampSort('last_edited_time', sort_by_last_edited_time),
        page_size
    ).execute()
    if entity == 'page':
        element_type = Page
    elif entity == 'database':
        element_type = Database
    else:
        element_type = Page | Database

    def it():
        for data in contents_it:
            if isinstance(data, DatabaseData):
                yield Database(data.id)
            elif isinstance(data, PageData):
                yield Page(data.id)
            else:
                raise RuntimeError(f"invalid class. {data=}")
        return

    return Paginator(element_type, it())
