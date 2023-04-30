from __future__ import annotations

from datetime import datetime
from typing import Generic, Iterator, Optional, TypeVar, overload, Literal, ClassVar

from typing_extensions import Self

from notion_df.object.block import BlockType, ResponseBlock, ChildPageBlockType
from notion_df.object.common import UUID, Icon
from notion_df.object.database import ResponseDatabase, DatabaseProperty
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.page import ResponsePage, PageProperty
from notion_df.object.parent import ResponseParent
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.object.user import User
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem
from notion_df.util.exception import NotionDfKeyError


class BaseBlock:
    # noinspection PyShadowingBuiltins
    def __init__(self, token: str, id: UUID):
        self.token = token
        self.id = id
        self._parent: Optional[ResponseParent] = None


class _AttributeAccessMode:
    ModeType = Literal['modified_first', 'initial', 'modified']
    now: ClassVar[ModeType] = 'modified_first'

    def __init__(self, this: ModeType):
        self.this = this

    def __enter__(self):
        type(self).now = self.this

    def __exit__(self):
        type(self).now = 'modified_first'


_VT = TypeVar('_VT')


class Attribute(Generic[_VT]):
    def __init__(self):
        self._modified: dict[BaseBlock, _VT] = {}
        self._initial: dict[BaseBlock, _VT] = {}

    @overload
    def __get__(self, instance: BaseBlock, owner: type[BaseBlock]) -> _VT:
        ...

    @overload
    def __get__(self, instance: None, owner: type[BaseBlock]) -> Self:
        ...

    def __get__(self, instance: Optional[BaseBlock], owner: type[BaseBlock]):
        if instance is None:
            return self
        match _AttributeAccessMode.now:
            case 'modified_first':
                if instance in self._modified:  # can be modified into None
                    return self._modified[instance]
                return self._initial.get(instance, None)
            case 'initial':
                return self._initial.get(instance, None)
            case 'modified':
                return self._modified.get(instance, None)

    def __set__(self, instance: BaseBlock, value: _VT) -> None:
        match _AttributeAccessMode.now:
            case 'initial':
                self._initial[instance] = value
            case _:
                self._modified[instance] = value


def _get_parent_block(token: str, parent: ResponseParent) -> Block | Database | Page | None:
    match parent.typename:
        case 'block_id':
            return Block(token, parent.id)
        case 'database_id':
            return Database(token, parent.id)
        case 'page_id':
            return Page(token, parent.id)


Property_T = TypeVar('Property_T', bound=(PageProperty | DatabaseProperty))


class Properties(Generic[Property_T]):
    # TODO: rewrite Properties with Attribute
    def __init__(self, serialized: dict[str, Property_T]):
        self._serialized = serialized

    @property
    def serialized(self) -> dict[str, Property_T]:
        return self._serialized

    def __iter__(self) -> Iterator[Property_T]:
        return iter(self._serialized.values())

    def __getitem__(self, key: str | Property_T) -> Property_T:
        if isinstance(key, str):
            return self._serialized[key]
        if isinstance(key, PageProperty) or isinstance(key, DatabaseProperty):
            return self._serialized[key.name]
        raise NotionDfKeyError(key)

    def append(self, prop: Property_T) -> None:
        self._serialized[prop.name] = prop

    def pop(self, prop: Property_T) -> Property_T:
        return self._serialized[prop.name]


class Block(BaseBlock):
    # TODO: resolve type hinting issue. consider using [ dataclass + data descriptor ]
    #  also, It would be great if I mark certain attrs as 'fixed' (such as 'created_time')
    parent: Optional[Page] = Attribute()
    created_time: datetime = Attribute()
    last_edited_time: datetime = Attribute()
    created_by: User = Attribute()
    last_edited_by: User = Attribute()
    has_children: bool = Attribute()
    archived: bool = Attribute()
    block_type: BlockType = Attribute()
    children: list[Block] = Attribute()

    def send_response_block(self, response_block: ResponseBlock) -> Block:
        with _AttributeAccessMode('initial'):
            self.parent = _get_parent_block(self.token, response_block.parent)
            self.created_time = response_block.created_time
            self.last_edited_time = response_block.last_edited_time
            self.created_by = response_block.created_by
            self.last_edited_by = response_block.last_edited_by
            self.has_children = response_block.has_children
            self.archived = response_block.archived
            self.block_type = response_block.block_type
        return self

    def send_child_response_block_list(self, response_block_list: list[ResponseBlock]) -> list[Block]:
        if not getattr(self, 'children', None):
            self.children = []
        new_children = []
        for response_block in response_block_list:
            block = Block(self.token, response_block.id)
            block.send_response_block(response_block)
            self.children.append(block)
            new_children.append(block)
        return new_children

    def retrieve(self) -> Self:
        response_block = RetrieveBlock(self.token, self.id).execute()
        return self.send_response_block(response_block)

    def retrieve_children(self) -> list[Block]:
        response_block_list = RetrieveBlockChildren(self.token, self.id).execute()
        return self.send_child_response_block_list(response_block_list)

    def update(self) -> Self:
        with _AttributeAccessMode('modified'):
            response_block = UpdateBlock(self.token, self.id, self.block_type, self.archived).execute()
        return self.send_response_block(response_block)

    def delete(self) -> Self:
        response_block = DeleteBlock(self.token, self.id).execute()
        return self.send_response_block(response_block)

    def append_children(self, block_type_list: list[BlockType]) -> list[Block]:
        response_block_list = AppendBlockChildren(self.token, self.id, block_type_list).execute()
        return self.send_child_response_block_list(response_block_list)

    def create_child_page(self, properties: Optional[Properties[PageProperty]] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.token, ResponseParent('page_id', self.id),
                                   properties.serialized, children, icon, cover).execute()
        page = Page(self.token, response_page.id)
        page.send_response_page(response_page)
        return page

    def create_child_database(self, title: list[RichText], *,
                              properties: Optional[Properties[DatabaseProperty]] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        response_database = CreateDatabase(self.token, self.id, title, properties.serialized, icon, cover).execute()
        database = Database(self.token, response_database.id)
        return database.send_response_database(response_database)


class Database(BaseBlock):
    parent: Page | Block | None = Attribute()
    created_time: datetime = Attribute()
    last_edited_time: datetime = Attribute()
    icon: Icon = Attribute()
    cover: ExternalFile = Attribute()
    url: str = Attribute()
    title: list[RichText] = Attribute()
    properties: Properties[DatabaseProperty] = Attribute()
    """the dict keys are same as each property's name or id (depending on request)"""
    archived: bool = Attribute()
    is_inline: bool = Attribute()
    children: list[Page] = Attribute()

    def send_response_database(self, response_database: ResponseDatabase) -> Self:
        with _AttributeAccessMode('initial'):
            self.parent = _get_parent_block(self.token, response_database.parent)
            self.created_time = response_database.created_time
            self.last_edited_time = response_database.last_edited_time
            self.icon = response_database.icon
            self.cover = response_database.cover
            self.url = response_database.url
            self.title = response_database.title
            self.properties = Properties[DatabaseProperty](response_database.properties)
            self.archived = response_database.archived
            self.is_inline = response_database.is_inline
        return self

    def send_response_page_list(self, response_page_list: list[ResponsePage]) -> list[Page]:
        if not getattr(self, 'children', None):
            self.children = []
        new_children = []
        for response_page in response_page_list:
            page = Page(self.token, response_page.id)
            page.send_response_page(response_page)
            self.children.append(page)
            new_children.append(page)
        return new_children

    def update(self) -> Self:
        with _AttributeAccessMode('modified'):
            response_database = UpdateDatabase(self.token, self.id, self.title, self.properties.serialized).execute()
        return self.send_response_database(response_database)

    def retrieve(self) -> Self:
        response_database = RetrieveDatabase(self.token, self.id).execute()
        return self.send_response_database(response_database)

    # noinspection PyShadowingBuiltins
    def query(self, filter: Filter, sort: list[Sort], page_size: int = -1) -> list[Page]:
        response_page_list = QueryDatabase(self.token, self.id, filter, sort, page_size).execute()
        return self.send_response_page_list(response_page_list)

    def create_child_page(self, properties: Optional[Properties[PageProperty]] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.token, ResponseParent('database_id', self.id),
                                   properties.serialized, children, icon, cover).execute()
        page = Page(self.token, response_page.id)
        page.send_response_page(response_page)
        return page


class Page(BaseBlock):
    parent: Block | Database | None = Attribute()
    created_time: datetime = Attribute()
    last_edited_time: datetime = Attribute()
    created_by: User = Attribute()
    last_edited_by: User = Attribute()
    archived: bool = Attribute()
    icon: Icon = Attribute()
    cover: ExternalFile = Attribute()
    url: str = Attribute()
    properties: Properties[PageProperty] = Attribute()

    def as_block(self) -> Block:
        block = Block(self.token, self.id)
        with _AttributeAccessMode('initial'):
            block.block_type = ChildPageBlockType('')
            block.created_time = self.created_time
            block.last_edited_time = self.last_edited_time
            block.created_by = self.created_by
            block.last_edited_by = self.last_edited_by
            block.archived = self.archived
        return block

    def send_response_page(self, response_page: ResponsePage) -> Self:
        self.parent = _get_parent_block(self.token, response_page.parent)
        self.created_time = response_page.created_time
        self.last_edited_time = response_page.last_edited_time
        self.created_by = response_page.created_by
        self.last_edited_by = response_page.last_edited_by
        self.icon = response_page.icon
        self.cover = response_page.cover
        self.url = response_page.url
        self.properties = Properties[PageProperty](response_page.properties)
        self.archived = response_page.archived
        return self

    def update(self) -> Self:
        response_page = UpdatePage(self.token, self.id, self.properties.serialized,
                                   self.icon, self.cover, self.archived).execute()
        return self.send_response_page(response_page)

    def retrieve(self) -> Self:
        response_page = RetrievePage(self.token, self.id).execute()
        return self.send_response_page(response_page)

    def retrieve_property_item(self, prop_id: UUID | PageProperty, page_size: int = -1) -> PageProperty:
        if isinstance(prop_id, PageProperty):
            prop_id = prop_id.id
        response_page_property = RetrievePagePropertyItem(self.token, self.id, prop_id, page_size).execute()
        self.properties.append(response_page_property)
        return response_page_property
