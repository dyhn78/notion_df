from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Any, Optional

from notion_df.endpoint.core import Request, RequestSettings, Version, Method
from notion_df.object.block import BlockObject
from notion_df.object.core import Deserializable, resolve_by_keychain
from notion_df.object.file import ExternalFile
from notion_df.object.misc import UUID, Icon
from notion_df.object.page import PageObject, PageProperty
from notion_df.object.parent import Parent


@dataclass
class PageRetrieveRequest(Request[PageObject]):
    """https://developers.notion.com/reference/retrieve-a-database"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class PageCreateRequest(Request[PageObject]):
    """https://developers.notion.com/reference/create-a-database"""
    parent: Parent
    icon: Icon
    cover: ExternalFile
    properties: dict[str, PageProperty] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    children: list[BlockObject] = field()

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
class PageUpdateRequest(Request[PageObject]):
    """https://developers.notion.com/reference/update-a-database"""
    id: UUID
    icon: Icon
    cover: ExternalFile
    properties: dict[str, PageProperty] = field()
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
class PagePropertyResponse(Deserializable):
    property_item: PageProperty

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "property_item",
            "id": "kjPO",
            **self.property_item
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars) -> dict[str, Any]:
        return {'property_item': serialized}


@dataclass
class PagePropertyListResponse(Deserializable):
    property_item: PageProperty
    results: list[PagePropertyResponse]
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
class PagePropertyRetrieveRequest(Request[PagePropertyItemBaseResponse]):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    page_id: UUID
    property_id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self) -> Any:
        return
