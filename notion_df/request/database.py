from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from notion_df.object.common import Icon, UUID
from notion_df.object.database import DatabaseProperty, ResponseDatabase
from notion_df.object.file import ExternalFile
from notion_df.object.filter import Filter
from notion_df.object.page import ResponsePage
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.request.core import SingleRequest, RequestSettings, Version, Method, PaginatedRequest
from notion_df.util.collection import DictFilter


@dataclass
class RetrieveDatabase(SingleRequest[ResponseDatabase]):
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class CreateDatabase(SingleRequest[ResponseDatabase]):
    """https://developers.notion.com/reference/create-a-database"""
    parent_id: UUID
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = field(default_factory=dict)
    """the dict keys are same as each property's name or id (depending on request)"""
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
class UpdateDatabase(SingleRequest[ResponseDatabase]):
    id: UUID
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = None
    """the dict keys are same as each property's name or id (depending on request).
    put empty dictionary to delete all properties."""

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
class QueryDatabase(PaginatedRequest[ResponsePage]):
    id: UUID
    filter: Filter
    sort: list[Sort]
    page_size: int = -1

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/databases/{self.id}/query')

    def get_body(self) -> Any:
        return DictFilter.truthy({
            'filter': self.filter,
            'sorts': self.sort,
        })

    @classmethod
    def parse_response_data_list(cls, data_list: list[dict[str, Any]]) -> list[ResponsePage]:
        ret = []
        for data in data_list:
            for result in data['results']:
                ret.append(ResponsePage.deserialize(result))
        return ret
