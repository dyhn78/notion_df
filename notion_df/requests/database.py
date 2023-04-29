from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from notion_df.objects.database import DatabaseProperty, ResponseDatabase
from notion_df.objects.file import File
from notion_df.objects.filter import Filter
from notion_df.objects.misc import Icon, UUID
from notion_df.objects.page import ResponsePage
from notion_df.objects.rich_text import RichText
from notion_df.objects.sort import Sort
from notion_df.requests.core import SingleRequest, RequestSettings, Version, Method, PaginatedRequest
from notion_df.utils.collection import DictFilter


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
    cover: Optional[File] = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               'https://api.notion.com/v1/databases/')

    def get_body(self) -> dict:
        d = {
            "parent": {
                "type": "page_id",
                "page_id": self.parent_id
            },
            "icon": self.icon,
            "cover": self.cover,
            "title": self.title,
            "properties": self.properties,
        }
        return DictFilter.truthy(d)


@dataclass
class UpdateDatabase(SingleRequest[ResponseDatabase]):
    database_id: UUID
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = field(default_factory=dict)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/databases/{self.database_id}')

    def get_url(self) -> str:
        return f'https://api.notion.com/v1/databases/{self.database_id}'

    def get_body(self) -> Any:
        d = {
            'title': self.title,
            'properties': self.properties,
        }
        return DictFilter.truthy(d)


@dataclass
class QueryDatabase(PaginatedRequest[list[ResponsePage]]):
    database_id: UUID
    filter: Filter
    sort: list[Sort]
    page_size: int = -1

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/databases/{self.database_id}/query')

    def get_body(self) -> Any:
        d = {
            'filter': self.filter,
            'sorts': self.sort,
        }
        return DictFilter.truthy(d)

    @classmethod
    def parse_response_data_list(cls, data_list: list[dict[str, Any]]) -> list[ResponsePage]:
        ret = []
        for data in data_list:
            for result in data['results']:
                ret.append(ResponsePage.deserialize(result))
        return ret
