from __future__ import annotations

from datetime import datetime
from typing import Optional, TypeVar, Union, Any, Literal, overload, Iterable
from uuid import UUID

from loguru import logger
from typing_extensions import Self

from notion_df.core.entity import RetrievableEntity, retrieve_if_undefined, CanBeParent, HasParent
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


class Workspace(CanBeParent):
    __instance: Optional[Self] = None

    def __new__(cls):
        return cls.__instance or super().__new__()

    def __repr__(self) -> str:
        return repr_object(self)

    def _repr_as_parent(self) -> str:
        return repr(self)


class Block(RetrievableEntity[BlockData], HasParent):
    data_cls = BlockData

    @property
    @retrieve_if_undefined
    def parent(self) -> Union[Block, Page, Workspace]:
        return self.data.parent

    @property
    @retrieve_if_undefined
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    @retrieve_if_undefined
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    @retrieve_if_undefined
    def created_by(self) -> PartialUser:
        return self.data.created_by

    @property
    @retrieve_if_undefined
    def last_edited_by(self) -> PartialUser:
        return self.data.last_edited_by

    @property
    @retrieve_if_undefined
    def has_children(self) -> Optional[bool]:
        """Note: the None value never occurs from direct server data. It only happens from Page.as_block()"""
        return self.data.has_children

    @property
    @retrieve_if_undefined
    def archived(self) -> bool:
        return self.data.archived

    @property
    @retrieve_if_undefined
    def value(self) -> BlockValue:
        return self.data.value

    def set_default_data(
            self,
            parent: Union[Block, Page, None] = undefined,
            created_time: datetime = undefined,
            last_edited_time: datetime = undefined,
            created_by: PartialUser = undefined,
            last_edited_by: PartialUser = undefined,
            has_children: bool = undefined,
            archived: bool = undefined,
            value: BlockValue = undefined,
    ) -> Self:
        return self._set_default_data(
            BlockData(self.id, parent, created_time, last_edited_time, created_by, last_edited_by, has_children,
                      archived, value))

    @staticmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        return get_block_id(id_or_url)

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)

    @staticmethod
    def _set_child_block_datas(block_datas: Iterable[BlockData]) -> Paginator[Block]:
        def it():
            for block_data in block_datas:
                yield Block(block_data.id).set_data(block_data)

        return Paginator(Block, it())

    def retrieve(self) -> Self:
        logger.info(f'Block.retrieve({self})')
        return self.set_data(RetrieveBlock(token, self.id).execute())

    def retrieve_children(self) -> Paginator[Block]:
        logger.info(f'Block.retrieve_children({self})')
        return self._set_child_block_datas(RetrieveBlockChildren(token, self.id).execute())

    def update(self, block_type: Optional[BlockValue], archived: Optional[bool]) -> Self:
        logger.info(f'Block.update({self})')
        return self.set_data(UpdateBlock(token, self.id, block_type, archived).execute())

    def delete(self) -> Self:
        logger.info(f'Block.delete({self})')
        return self.set_data(DeleteBlock(token, self.id).execute())

    def append_children(self, child_values: list[BlockValue]) -> list[Block]:
        logger.info(f'Block.append_children({self})')
        if not child_values:
            return []
        return list(self._set_child_block_datas(AppendBlockChildren(token, self.id, child_values).execute()))

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        logger.info(f'Block.create_child_database({self})')
        data = CreateDatabase(token, self.id, title, properties, icon, cover).execute()
        return Database(data.id).set_data(data)


class Database(RetrievableEntity[DatabaseData], HasParent):
    data_cls = DatabaseData

    @property
    @retrieve_if_undefined
    def parent(self) -> Union[Block, Page, Workspace]:
        return self.data.parent

    @property
    @retrieve_if_undefined
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    @retrieve_if_undefined
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    @retrieve_if_undefined
    def icon(self) -> Optional[Icon]:
        return self.data.icon

    @property
    @retrieve_if_undefined
    def cover(self) -> Optional[File]:
        return self.data.cover

    @property
    @retrieve_if_undefined
    def url(self) -> str:
        return self.data.url

    @property
    @retrieve_if_undefined
    def title(self) -> RichText:
        return self.data.title

    @property
    @retrieve_if_undefined
    def properties(self) -> DatabaseProperties:
        return self.data.properties

    @property
    @retrieve_if_undefined
    def archived(self) -> bool:
        return self.data.archived

    @property
    @retrieve_if_undefined
    def is_inline(self) -> bool:
        return self.data.is_inline

    def set_default_data(
            self,
            parent: Union[Block, Page, None] = undefined,
            created_time: datetime = undefined,
            last_edited_time: datetime = undefined,
            icon: Optional[Icon] = undefined,
            cover: Optional[File] = undefined,
            url: str = undefined,
            title: RichText = undefined,
            properties: DatabaseProperties = undefined,
            archived: bool = undefined,
            is_inline: bool = undefined,
    ) -> Self:
        return self._set_default_data(
            DatabaseData(self.id, parent, created_time, last_edited_time, icon, cover, url, title, properties, archived,
                         is_inline))

    @staticmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        if self.local_data:
            return repr_object(self, title=self.local_data.title.plain_text,
                               url=self.local_data.url, parent=self._repr_parent())
        else:
            return repr_object(self, id=self.id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        if self.local_data:
            return repr_object(self, title=self.local_data.title.plain_text)
        else:
            return repr_object(self, id=self.id)

    @staticmethod
    def _set_child_page_data(page_data_it: Iterable[PageData]) -> Paginator[Page]:
        def it():
            for page_data in page_data_it:
                yield Page(page_data.id).set_data(page_data)

        return Paginator(Page, it())

    def retrieve(self) -> Self:
        logger.info(f'Database.retrieve({self})')
        return self.set_data(RetrieveDatabase(token, self.id).execute())

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: Optional[int] = None) -> Paginator[Page]:
        logger.info(f'Database.query({self})')
        return self._set_child_page_data(QueryDatabase(token, self.id, filter, sort, page_size).execute())

    def update(self, title: RichText, properties: DatabaseProperties) -> Database:
        logger.info(f'Database.update({self})')
        return self.set_data(UpdateDatabase(token, self.id, title, properties).execute())

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        logger.info(f'Database.create_child_page({self})')
        page_data = CreatePage(token, PartialParent('database_id', self.id),
                               properties, children, icon, cover).execute()
        return Page(page_data.id).set_data(page_data)


class Page(RetrievableEntity[PageData], HasParent):
    data_cls = PageData

    @property
    @retrieve_if_undefined
    def parent(self) -> Union[Block, Database, Page, Workspace]:
        return self.data.parent

    @property
    @retrieve_if_undefined
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    @retrieve_if_undefined
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    @retrieve_if_undefined
    def created_by(self) -> PartialUser:
        return self.data.created_by

    @property
    @retrieve_if_undefined
    def last_edited_by(self) -> PartialUser:
        return self.data.last_edited_by

    @property
    @retrieve_if_undefined
    def icon(self) -> Optional[Icon]:
        return self.data.icon

    @property
    @retrieve_if_undefined
    def cover(self) -> Optional[File]:
        return self.data.cover

    @property
    @retrieve_if_undefined
    def url(self) -> str:
        return self.data.url

    @property
    @retrieve_if_undefined
    def archived(self) -> bool:
        return self.data.archived

    @property
    @retrieve_if_undefined
    def properties(self) -> PageProperties:
        return self.data.properties

    def set_default_data(self,
                         parent: Union[Block, Database, Page, None] = undefined,
                         created_time: datetime = undefined,
                         last_edited_time: datetime = undefined,
                         created_by: PartialUser = undefined,
                         last_edited_by: PartialUser = undefined,
                         icon: Optional[Icon] = undefined,
                         cover: Optional[File] = undefined,
                         url: str = undefined,
                         archived: bool = undefined,
                         properties: PageProperties = undefined,
                         ) -> Self:
        return self._set_default_data(
            PageData(self.id, parent, created_time, last_edited_time, created_by, last_edited_by, icon, cover, url,
                     archived, properties))

    @staticmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        # TODO refactor
        try:
            if not self.local_data:
                raise AttributeError
            title = self.local_data.properties.title.plain_text
            _id = undefined
        except (NotionDfKeyError, AttributeError):
            title = undefined
            _id = self.id
        return repr_object(self, title=title, url=self.local_data.url,
                           id=_id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        try:
            title = self.local_data.properties.title.plain_text
            return repr_object(self, title=title)
        except (NotionDfKeyError, AttributeError):
            return repr_object(self, id=self.id)

    def as_block(self) -> Block:
        block = Block(self.id)
        block.set_default_data(
            parent=self.data.parent,
            created_time=self.data.created_time,
            last_edited_time=self.data.last_edited_time,
            created_by=self.data.created_by,
            last_edited_by=self.data.last_edited_by,
            archived=self.data.archived,
            value=(block.data.value if block.data else ChildPageBlockValue(title='')),
        )
        return block

    def retrieve(self) -> Self:
        logger.info(f'Page.retrieve({self})')
        return self.set_data(RetrievePage(token, self.id).execute())

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
        return self.set_data(UpdatePage(token, self.id, properties, icon, cover, archived).execute())

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockValue]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        logger.info(f'Page.create_child_page({self})')
        page_data = CreatePage(token, PartialParent('page_id', self.id), properties, children, icon, cover).execute()
        return Page(page_data.id).set_data(page_data)

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
