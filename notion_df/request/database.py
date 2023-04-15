from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from notion_df.request.core import Request, RequestSettings, Version, Method
from notion_df.response.database import ResponseDatabase, DatabaseProperty, ResponseQueryDatabase
from notion_df.response.file import File
from notion_df.response.filter import Filter
from notion_df.response.misc import Icon, UUID
from notion_df.response.rich_text import RichText
from notion_df.response.sort import Sort
from notion_df.util.collection import filter_truthy


@dataclass
class RetrieveDatabase(Request[ResponseDatabase]):
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class CreateDatabase(Request[ResponseDatabase]):
    """https://developers.notion.com/reference/create-a-database"""
    parent_id: UUID
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = field(default_factory=dict)
    """the dict keys are same as each property's name or id (depending on request)"""
    icon: Optional[Icon] = field(default=None)
    cover: Optional[File] = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               'https://api.notion.com/v1/databases/')

    def get_body(self) -> dict:
        return filter_truthy({
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
class UpdateDatabase(Request[ResponseDatabase]):
    database_id: UUID
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = field(default_factory=dict)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/databases/{self.database_id}')

    def get_url(self) -> str:
        return f'https://api.notion.com/v1/databases/{self.database_id}'

    def get_body(self) -> Any:
        return filter_truthy({
            'title': self.title,
            'properties': self.properties,
        })


@dataclass
class QueryDatabase(Request[ResponseQueryDatabase]):
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
        return filter_truthy({
            'filter': self.filter,
            'sorts': self.sort,
            'start_cursor': self.start_cursor,
            'page_size': self.page_size,
        })
