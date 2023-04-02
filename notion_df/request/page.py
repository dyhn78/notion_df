from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from notion_df.object.block_item import BlockItem
from notion_df.object.core import Deserializable, resolve_by_keychain
from notion_df.object.file import ExternalFile
from notion_df.object.misc import UUID, Icon
from notion_df.object.parent import Parent
from notion_df.object.property_item import PropertyItem
from notion_df.object.rich_text import RichText
from notion_df.object.user import PartialUser
from notion_df.request.core import Request, RequestSettings, Version, Method


@dataclass
class PageResponse(Deserializable):
    id: UUID
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    icon: Icon
    cover: ExternalFile
    url: str
    title: list[RichText]
    properties: dict[str, PropertyItem] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    parent: Parent
    archived: bool
    is_inline: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "page",
            "id": self.id,
            "created_time": self.created_by,
            "last_edited_time": self.last_edited_by,
            "created_by": self.created_by,
            "last_edited_by": self.last_edited_by,
            "cover": self.cover,
            "icon": self.icon,
            "parent": self.parent,
            "archived": False,
            "properties": self.properties,
            "url": self.url,
        }


@dataclass
class PageRetrieveRequest(Request[PageResponse]):
    """https://developers.notion.com/reference/retrieve-a-database"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class PageCreateRequest(Request[PageResponse]):
    """https://developers.notion.com/reference/create-a-database"""
    parent: Parent
    icon: Icon
    cover: ExternalFile
    properties: dict[str, PropertyItem] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    children: list[BlockItem] = field()

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/pages')

    def get_body(self) -> Any:
        return {
            "parent": self.parent,
            "icon": self.icon,
            "cover": self.cover,
            "properties": self.properties,
            "children": self.children,
        }


@dataclass
class PageUpdateRequest(Request[PageResponse]):
    """https://developers.notion.com/reference/update-a-database"""
    id: UUID
    icon: Icon
    cover: ExternalFile
    properties: dict[str, PropertyItem] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    archived: bool

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> Any:
        return {
            "icon": self.icon,
            "cover": self.cover,
            "properties": self.properties,
            "archived": self.archived,
        }


@resolve_by_keychain('object')
class PagePropertyItemBaseResponse(Deserializable, metaclass=ABCMeta):
    pass


@dataclass
class PagePropertyItemResponse(Deserializable):
    property_item: PropertyItem

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "property_item",
            "id": "kjPO",
            **self.property_item
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any]) -> dict[str, Any]:
        return {'property_item': serialized}


@dataclass
class PagePropertyItemListResponse(Deserializable):
    property_item: PropertyItem
    results: list[PagePropertyItemResponse]
    next_cursor: Optional[str]
    has_more: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "list",
            "results": self.results,
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
            "property_item": self.property_item,
            "type": "property_item"
        }


@dataclass
class PagePropertyItemRetrieveRequest(Request[PagePropertyItemBaseResponse]):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    page_id: UUID
    property_id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self) -> Any:
        return
