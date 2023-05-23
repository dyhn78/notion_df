from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from notion_df.object.block import DatabaseResponse, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile
from notion_df.object.filter import Filter
from notion_df.object.property import DatabaseProperties
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.request.request_core import SingleRequest, RequestSettings, Version, Method, PaginatedRequest
from notion_df.util.collection import DictFilter


@dataclass
class RetrieveDatabase(SingleRequest[DatabaseResponse]):
    response_type = DatabaseResponse
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class CreateDatabase(SingleRequest[DatabaseResponse]):
    """https://developers.notion.com/reference/create-a-database"""
    response_type = DatabaseResponse
    parent_id: UUID
    title: RichText
    properties: Optional[DatabaseProperties] = field(default_factory=DatabaseProperties)
    icon: Optional[Icon] = field(default=None)
    cover: Optional[ExternalFile] = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               'https://api.notion.com/v1/databases/')

    def get_body(self) -> dict:
        return DictFilter.not_none({
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
class UpdateDatabase(SingleRequest[DatabaseResponse]):
    response_type = DatabaseResponse
    id: UUID
    title: RichText
    properties: Optional[DatabaseProperties] = None
    """send empty DatabaseProperties to delete all properties."""

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_url(self) -> str:
        return f'https://api.notion.com/v1/databases/{self.id}'

    def get_body(self) -> Any:
        return DictFilter.not_none({
            'title': self.title,
            'properties': self.properties,
        })


@dataclass
class QueryDatabase(PaginatedRequest[PageResponse]):
    response_element_type = PageResponse
    id: UUID
    filter: Filter
    sort: list[Sort]
    page_size: int = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/databases/{self.id}/query')

    def get_body(self) -> Any:
        return DictFilter.truthy({
            'filter': self.filter,
            'sorts': self.sort,
        })
