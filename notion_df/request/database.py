from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from notion_df.request.core import Request, RequestSettings, Version, Method
from notion_df.request.page import PageResponse
from notion_df.resource.core import Deserializable
from notion_df.resource.file import File, ExternalFile
from notion_df.resource.filter import Filter
from notion_df.resource.misc import Icon, UUID
from notion_df.resource.parent import Parent
from notion_df.resource.property import PropertySchema, PropertySchemaFull
from notion_df.resource.rich_text import RichText
from notion_df.resource.sort import Sort
from notion_df.util.misc import dict_filter_truthy


@dataclass
class DatabaseQueryResponse(Deserializable):
    results: list[PageResponse]
    next_cursor: Optional[str]
    has_more: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'object': 'list',
            'results': self.results,
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
            "type": "page",
            "page": {}
        }


@dataclass
class DatabaseQueryRequest(Request[DatabaseQueryResponse]):
    database_id: UUID
    filter: Filter
    sort: list[Sort]
    start_cursor: Optional[str] = None
    page_size: int = 100

    def __post_init__(self):
        if self.page_size > 100:
            self.page_size = 100

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/databases/{self.database_id}/query')

    def get_body(self) -> Any:
        return dict_filter_truthy({
            'filter': self.filter,
            'sorts': self.sort,
            'start_cursor': self.start_cursor,
            'page_size': self.page_size,
        })


@dataclass
class DatabaseResponse(Deserializable):
    id: UUID
    url: str
    title: RichText
    properties: dict[str, PropertySchemaFull] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    parent: Parent
    icon: Icon
    cover: ExternalFile
    created_time: datetime
    last_edited_time: datetime
    archived: bool
    is_inline: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": 'database',
            "id": self.id,
            "created_time": self.created_time,
            "last_edited_time": self.last_edited_time,
            "icon": self.icon,
            "cover": self.cover,
            "url": self.url,
            "title": self.title,
            "properties": self.properties,
            "parent": self.parent,
            "archived": self.archived,
            "is_inline": self.is_inline,
        }


@dataclass
class DatabaseCreateRequest(Request[DatabaseResponse]):
    """https://developers.notion.com/reference/create-a-database"""
    parent_id: UUID
    title: list[RichText] = field(default_factory=list)
    properties: dict[str, PropertySchema] = field(default_factory=dict)
    icon: Optional[Icon] = field(default=None)
    cover: Optional[File] = field(default=None)
    """the dict keys are same as each property's name or id (depending on request)"""

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               'https://api.notion.com/v1/databases/')

    def get_body(self) -> dict:
        return dict_filter_truthy({
            "parent": {
                "type": "page_id",
                "page_id": self.parent_id
            },
            "icon": self.icon,
            "cover": self.cover,
            "title": self.title,
            "properties": self.properties,
        })


@dataclass
class DatabaseUpdateRequest(Request[DatabaseResponse]):
    database_id: UUID
    title: list[RichText] = field(default_factory=list)
    properties: dict[str, PropertySchema] = field(default_factory=dict)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/databases/{self.database_id}')

    def get_url(self) -> str:
        return f'https://api.notion.com/v1/databases/{self.database_id}'

    def get_body(self) -> Any:
        return dict_filter_truthy({
            'title': self.title,
            'properties': self.properties,
        })


@dataclass
class DatabaseRetrieveRequest(Request[DatabaseResponse]):
    database_id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.database_id}')

    def get_body(self) -> Any:
        return
