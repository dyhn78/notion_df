from __future__ import annotations

from datetime import datetime
from typing import Optional, TypeVar, Union, Any, Literal, overload, cast, Generic
from uuid import UUID

from loguru import logger
from typing_extensions import Self

from notion_df.contents import BlockContents
from notion_df.core.collection import Paginator
from notion_df.core.entity_core import RetrievableEntity, retrieve_on_demand, CanBeParent, \
    HasParent
from notion_df.core.exception import ImplementationError
from notion_df.core.request_core import RequestError
from notion_df.core.struct import undefined, repr_object
from notion_df.core.uuid_parser import get_page_or_database_id, get_block_id
from notion_df.core.variable import token
from notion_df.data import BlockData, DatabaseData, PageData
from notion_df.file import ExternalFile, File
from notion_df.filter import Filter
from notion_df.misc import Icon, PartialParent, Emoji
from notion_df.property import Property, PageProperties, DatabaseProperties, \
    PPVT
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, \
    RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, \
    QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, \
    RetrievePagePropertyItem
from notion_df.request.search import SearchByTitle
from notion_df.rich_text import RichText
from notion_df.sort import Sort, TimestampSort, Direction
from notion_df.user import PartialUser

BlockT = TypeVar('BlockT', bound='Block')
DatabaseT = TypeVar('DatabaseT', bound='Database')
PageT = TypeVar('PageT', bound='Page')


class Workspace(CanBeParent):
    # TODO: allow multiple workspace, corresponding to multiple tokens
    """the singleton representing the workspace root."""
    __instance: Optional[Self] = None
    parent = None

    def __new__(cls) -> Workspace:
        return cls.__instance or super().__new__(cls)

    def __repr__(self) -> str:
        return repr_object(self)

    def _repr_as_parent(self) -> str:
        return repr(self)


class Block(RetrievableEntity[BlockData], HasParent, Generic[BlockT]):
    data_cls = BlockData

    @property
    @retrieve_on_demand
    def parent(self) -> Union[Block, Page, Workspace]:
        return self.data.parent

    @property
    @retrieve_on_demand
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    @retrieve_on_demand
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    @retrieve_on_demand
    def created_by(self) -> PartialUser:
        return self.data.created_by

    @property
    @retrieve_on_demand
    def last_edited_by(self) -> PartialUser:
        return self.data.last_edited_by

    @property
    @retrieve_on_demand
    def has_children(self) -> Optional[bool]:
        """Note: the None value never occurs from direct server data. It only happens from Page.as_block()"""
        return self.data.has_children

    @property
    @retrieve_on_demand
    def archived(self) -> bool:
        return self.data.archived

    @property
    @retrieve_on_demand
    def contents(self) -> BlockContents:
        return self.data.contents

    @staticmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        return get_block_id(id_or_url)

    def _repr_as_parent(self) -> str:
        return repr_object(self, id=self.id)

    def retrieve(self) -> Self:
        logger.info(f'Block.retrieve({self})')
        RetrieveBlock(token, self.id).execute()
        return self

    def retrieve_children(self) -> Paginator[Block]:
        logger.info(f'Block.retrieve_children({self})')
        return Paginator(Block, (Block(block_data.id) for block_data in
                                 RetrieveBlockChildren(token, self.id).execute()))

    def update(self, block_type: Optional[BlockContents],
               archived: Optional[bool]) -> Self:
        logger.info(f'Block.update({self})')
        UpdateBlock(token, self.id, block_type, archived).execute()
        return self

    def delete(self, ignore_archived: bool = False) -> Self:
        logger.info(f'Block.delete({self})')
        try:
            DeleteBlock(token, self.id).execute()
        except RequestError as e:
            if ignore_archived and "Can't edit block that is archived." in e.message:
                logger.info(f'ignore already archived block {self}')
            else:
                raise e
        return self

    def append_children(self, child_values: list[BlockContents]) -> list[Block]:
        logger.info(f'Block.append_children({self})')
        if not child_values:
            return []
        return [Block(block_data.id) for block_data in
                AppendBlockChildren(token, self.id, child_values).execute()]

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None,
                              cover: Optional[File] = None) -> Database:
        logger.info(f'Block.create_child_database({self})')
        return Database(
            CreateDatabase(token, self.id, title, properties, icon, cover).execute().id)


class Database(RetrievableEntity[DatabaseData], HasParent, Generic[PageT]):
    data_cls = DatabaseData

    @property
    @retrieve_on_demand
    def parent(self) -> Union[Block, Page, Workspace]:
        return self.data.parent

    @property
    @retrieve_on_demand
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    @retrieve_on_demand
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    @retrieve_on_demand
    def icon(self) -> Optional[Icon]:
        return self.data.icon

    @property
    @retrieve_on_demand
    def emoji_value(self) -> str:
        return self.data.icon.value if isinstance(self.data.icon, Emoji) else ""

    @property
    @retrieve_on_demand
    def cover(self) -> Optional[File]:
        return self.data.cover

    @property
    @retrieve_on_demand
    def url(self) -> str:
        return self.data.url

    @property
    @retrieve_on_demand
    def title(self) -> RichText:
        return self.data.title

    @property
    @retrieve_on_demand
    def properties(self) -> DatabaseProperties:
        return self.data.properties

    @property
    @retrieve_on_demand
    def archived(self) -> bool:
        return self.data.archived

    @property
    @retrieve_on_demand
    def is_inline(self) -> bool:
        return self.data.is_inline

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

    def retrieve(self) -> Self:
        logger.info(f'Database.retrieve({self})')
        RetrieveDatabase(token, self.id).execute()
        return self

    def update(self, title: RichText, properties: DatabaseProperties) -> Database:
        logger.info(f'Database.update({self})')
        UpdateDatabase(token, self.id, title, properties).execute()
        return self

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockContents]] = None,
                          icon: Optional[Icon] = None,
                          cover: Optional[File] = None) -> Page:
        logger.info(f'Database.create_child_page({self})')
        return Page(CreatePage(token, PartialParent('database_id', self.id),
                               properties, children, icon, cover).execute().id)

    # noinspection PyShadowingBuiltins
    def query(self, filter: Optional[Filter] = None, sort: Optional[list[Sort]] = None,
              page_size: Optional[int] = None) -> Paginator[PageT]:
        logger.info(f'Database.query({self})')
        return Paginator(Page, (Page(page_data.id) for page_data in
                                QueryDatabase(token, self.id, filter, sort,
                                              page_size).execute()))


class Page(RetrievableEntity[PageData], HasParent):
    data_cls = PageData

    @property
    @retrieve_on_demand
    def parent(self) -> Union[Block, Database, Page, Workspace]:
        return self.data.parent

    @property
    @retrieve_on_demand
    def created_time(self) -> datetime:
        return self.data.created_time

    @property
    @retrieve_on_demand
    def last_edited_time(self) -> datetime:
        return self.data.last_edited_time

    @property
    @retrieve_on_demand
    def created_by(self) -> PartialUser:
        return self.data.created_by

    @property
    @retrieve_on_demand
    def last_edited_by(self) -> PartialUser:
        return self.data.last_edited_by

    @property
    @retrieve_on_demand
    def icon(self) -> Optional[Icon]:
        return self.data.icon

    @property
    @retrieve_on_demand
    def cover(self) -> Optional[File]:
        return self.data.cover

    @property
    @retrieve_on_demand
    def url(self) -> str:
        return self.data.url

    @property
    @retrieve_on_demand
    def archived(self) -> bool:
        return self.data.archived

    @property
    @retrieve_on_demand
    def properties(self) -> PageProperties:
        return self.data.properties

    @property
    def title(self) -> RichText:
        if ret := self.properties.title:
            return ret
        return self.retrieve().properties.title

    @staticmethod
    def _get_id(id_or_url: Union[UUID, str]) -> UUID:
        return get_page_or_database_id(id_or_url)

    def __repr__(self) -> str:
        if self.local_data and self.local_data.properties.title is not None:
            return repr_object(self, title=self.local_data.properties.title.plain_text,
                               url=self.local_data.url, parent=self._repr_parent())
        else:
            return repr_object(self, id=self.id, parent=self._repr_parent())

    def _repr_as_parent(self) -> str:
        try:
            return repr_object(self, title=self.local_data.properties.title.plain_text)
        except (KeyError, AttributeError):
            return repr_object(self, id=self.id)

    def as_block(self) -> Block:
        block = Block(self.id)
        BlockData(
            id=self.id,
            parent=self.data.parent,
            created_time=self.data.created_time,
            last_edited_time=self.data.last_edited_time,
            created_by=self.data.created_by,
            last_edited_by=self.data.last_edited_by,
            archived=self.data.archived,
            has_children=undefined,
            contents=undefined,
            preview=True
        ).set_preview()
        return block

    def retrieve(self) -> Self:
        logger.info(f'Page.retrieve({self})')
        RetrievePage(token, self.id).execute()
        return self

    def retrieve_property_item(
            self, property_id: str | Property[Any, PPVT, Any]) -> PPVT:
        logger.info(f'Page.retrieve_property_item({self}, property_id="{property_id}")')
        if isinstance(prop := property_id, Property):
            property_id = prop.id
            if property_id is None:
                raise ImplementationError(
                    "property.id is None. if you do not know the property id, retrieve the parent database first.",
                    {"self": self})
            _, prop_value, prop_serialized = RetrievePagePropertyItem(token, self.id,
                                                                      property_id).execute()
        else:
            prop, prop_value, prop_serialized = RetrievePagePropertyItem(token, self.id,
                                                                         property_id).execute()
        if self.data:
            if not prop.name:
                # noinspection PyProtectedMember
                prop = self.data.properties._prop_by_id[prop.id]
            self.data.properties[prop] = prop_value
            cast(dict[str, Any], self.data.raw["properties"][prop.name]).update(
                prop_serialized)
        return prop_value

    def update(self, properties: Optional[PageProperties] = None,
               icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None,
               archived: Optional[bool] = None) -> Self:
        logger.info(f'Page.update({self})')
        UpdatePage(token, self.id, properties, icon, cover, archived).execute()
        return self

    def create_child_page(self, properties: Optional[PageProperties] = None,
                          children: Optional[list[BlockContents]] = None,
                          icon: Optional[Icon] = None,
                          cover: Optional[File] = None) -> Page:
        logger.info(f'Page.create_child_page({self})')
        return Page(CreatePage(token, PartialParent('page_id', self.id), properties,
                               children, icon, cover).execute().id)

    def create_child_database(self, title: RichText, *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None,
                              cover: Optional[File] = None) -> Database:
        logger.info(f'Page.create_child_database({self})')
        return self.as_block().create_child_database(title, properties=properties,
                                                     icon=icon, cover=cover)


@overload
def search_by_title(query: str, entity: Literal['page'],
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> Paginator[Page]:
    ...


@overload
def search_by_title(query: str, entity: Literal['database'],
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> Paginator[Database]:
    ...


@overload
def search_by_title(query: str, entity: Literal[None],
                    sort_by_last_edited_time: Direction = 'descending',
                    page_size: int = None) -> Paginator[Union[Page, Database]]:
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
            match data:
                case DatabaseData():
                    yield Database(data.id)
                case PageData():
                    yield Page(data.id)
                case _:
                    raise RuntimeError(f"invalid class. {data=}")

    return Paginator(element_type, it())
