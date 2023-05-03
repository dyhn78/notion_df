from __future__ import annotations

from collections.abc import Sequence
from typing import Optional, TypeVar, Union

from typing_extensions import Self

from notion_df.object.block import BlockType, BlockResponse, ChildPageBlockType
from notion_df.object.common import UUID, Icon, Properties
from notion_df.object.database import DatabaseResponse, DatabaseProperties
from notion_df.object.file import ExternalFile, File
from notion_df.object.filter import Filter
from notion_df.object.page import PageResponse, PageProperty, PageProperties
from notion_df.object.parent import ParentResponse
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.request.block import AppendBlockChildren, RetrieveBlock, RetrieveBlockChildren, UpdateBlock, DeleteBlock
from notion_df.request.database import CreateDatabase, UpdateDatabase, RetrieveDatabase, QueryDatabase
from notion_df.request.page import CreatePage, UpdatePage, RetrievePage, RetrievePagePropertyItem

_VT = TypeVar('_VT')


class BaseBlock:
    # noinspection PyShadowingBuiltins
    def __init__(self, token: str, id: UUID):
        self.token = token
        self.id = id


class Block(BaseBlock):
    last_response: Optional[BlockResponse]

    # noinspection PyShadowingBuiltins
    def __init__(self, token: str, id: UUID):
        super().__init__(token, id)
        self.last_response = None

    @property
    def parent(self) -> Union[Page, Block, None]:
        if self.last_response is None:
            return
        return self.last_response.parent.as_block(self.token)

    def _send_child_block_response_list(self, block_response_list: list[BlockResponse]) -> BlockChildren:
        block_list = []
        for block_response in block_response_list:
            block = Block(self.token, block_response.id)
            block.last_response = block_response
            block_list.append(block)
        return BlockChildren(block_list)

    def retrieve(self) -> Self:
        self.last_response = RetrieveBlock(self.token, self.id).execute()
        return self.last_response

    def retrieve_children(self) -> BlockChildren:
        block_response_list = RetrieveBlockChildren(self.token, self.id).execute()
        return self._send_child_block_response_list(block_response_list)

    def update(self, block_type: Optional[BlockType], archived: Optional[bool]) -> Self:
        self.last_response = UpdateBlock(self.token, self.id, block_type, archived).execute()
        return self.last_response

    def delete(self) -> Self:
        self.last_response = DeleteBlock(self.token, self.id).execute()
        return self.last_response

    def append_children(self, block_type_list: list[BlockType]) -> BlockChildren:
        block_response_list = AppendBlockChildren(self.token, self.id, block_type_list).execute()
        return self._send_child_block_response_list(block_response_list)

    def create_child_page(self, properties: Optional[Properties[PageProperty]] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.token, ParentResponse('page_id', self.id),
                                   properties, children, icon, cover).execute()
        page = Page(self.token, response_page.id)
        page.last_response = response_page
        return page

    def create_child_database(self, title: list[RichText], *,
                              properties: Optional[DatabaseProperties] = None,
                              icon: Optional[Icon] = None, cover: Optional[File] = None) -> Database:
        response_database = CreateDatabase(self.token, self.id, title, properties, icon, cover).execute()
        database = Database(self.token, response_database.id)
        database.last_response = response_database
        return database


class Database(BaseBlock):
    last_response: Optional[DatabaseResponse]

    # noinspection PyShadowingBuiltins
    def __init__(self, token: str, id: UUID):
        super().__init__(token, id)
        self.last_response = None

    @property
    def parent(self) -> Union[Page, Block, None]:
        if self.last_response is None:
            return
        return self.last_response.parent.as_block(self.token)

    def _send_child_page_response_list(self, page_response_list: list[PageResponse]) -> PageChildren:
        page_list = []
        for page_response in page_response_list:
            page = Page(self.token, page_response.id)
            page.last_response = page_response
        return PageChildren(page_list)

    def retrieve(self) -> Self:
        self.last_response = RetrieveDatabase(self.token, self.id).execute()
        return self.last_response

    # noinspection PyShadowingBuiltins
    def query(self, filter: Filter, sort: list[Sort], page_size: int = -1) -> Children[Page]:
        response_page_list = QueryDatabase(self.token, self.id, filter, sort, page_size).execute()
        return self._send_child_page_response_list(response_page_list)

    def update(self, title: list[RichText], properties: DatabaseProperties) -> Self:
        self.last_response = UpdateDatabase(self.token, self.id, title, properties).execute()
        return self.last_response

    def create_child_page(self, properties: Optional[Properties[PageProperty]] = None,
                          children: Optional[list[BlockType]] = None,
                          icon: Optional[Icon] = None, cover: Optional[File] = None) -> Page:
        response_page = CreatePage(self.token, ParentResponse('database_id', self.id),
                                   properties, children, icon, cover).execute()
        page = Page(self.token, response_page.id)
        page.last_response = response_page
        return page


class Page(BaseBlock):
    last_response: Optional[PageResponse]

    # noinspection PyShadowingBuiltins
    def __init__(self, token: str, id: UUID):
        super().__init__(token, id)
        self.last_response = None

    @property
    def parent(self) -> Union[Page, Block, None]:
        if self.last_response is None:
            return
        return self.last_response.parent.as_block(self.token)

    def as_block(self) -> Block:
        block = Block(self.token, self.id)
        if self.last_response:
            block.last_response = BlockResponse(
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
        return block

    def update(self, properties: Optional[PageProperties] = None, icon: Optional[Icon] = None,
               cover: Optional[ExternalFile] = None, archived: Optional[bool] = None) -> PageResponse:
        self.last_response = UpdatePage(self.token, self.id, properties, icon, cover, archived).execute()
        return self.last_response

    def retrieve(self) -> PageResponse:
        self.last_response = RetrievePage(self.token, self.id).execute()
        return self.last_response

    def retrieve_property_item(self, prop_id: UUID | PageProperty, page_size: int = -1) -> PageProperty:
        if isinstance(prop_id, PageProperty):
            prop_id = prop_id.id
        page_property = RetrievePagePropertyItem(self.token, self.id, prop_id, page_size).execute()
        return page_property


class Children(Sequence[_VT]):
    def __init__(self, values: list[_VT]):
        self._values: list[_VT] = values
        self._by_id: dict[UUID, _VT] = {child.id: child for child in self._values}

    def __getitem__(self, index_or_id: int | UUID) -> _VT:
        if isinstance(index_or_id, int):
            return self._values[index_or_id]
        elif isinstance(index_or_id, UUID):
            return self._by_id[index_or_id]
        else:
            raise TypeError(f"Invalid argument type. Expected int or UUID - {index_or_id}")

    def get(self, index_or_id: int | UUID) -> Optional[_VT]:
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
