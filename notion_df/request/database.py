from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from notion_df.core.request import SingleRequestBuilder, RequestSettings, Version, Method, PaginatedRequestBuilder
from notion_df.object.data import DatabaseData, PageData
from notion_df.object.file import ExternalFile
from notion_df.object.filter import Filter
from notion_df.object.misc import Icon
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.property import DatabaseProperties
from notion_df.util.collection import DictFilter


@dataclass
class RetrieveDatabase(SingleRequestBuilder[DatabaseData]):
    data_type = DatabaseData
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class CreateDatabase(SingleRequestBuilder[DatabaseData]):
    """https://developers.notion.com/reference/create-a-database"""
    data_type = DatabaseData
    parent_id: UUID
    title: RichText
    properties: Optional[DatabaseProperties] = field(default_factory=DatabaseProperties)
    icon: Optional[Icon] = field(default=None)
    cover: Optional[ExternalFile] = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               'databases/')

    def get_body(self) -> dict:
        return DictFilter.not_none({
            "parent": {
                "type": "page_id",
                "page_id": str(self.parent_id)
            },
            "icon": self.icon.serialize() if self.icon else None,
            "cover": self.cover.serialize() if self.cover else None,
            "title": self.title.serialize() if self.title else None,
            "properties": self.properties.serialize() if self.properties else None,
        })


@dataclass
class UpdateDatabase(SingleRequestBuilder[DatabaseData]):
    data_type = DatabaseData
    id: UUID
    title: RichText
    properties: Optional[DatabaseProperties] = None
    """send empty DatabaseProperties to delete all properties."""

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'databases/{self.id}')

    def get_url(self) -> str:
        return f'databases/{self.id}'

    def get_body(self) -> Any:
        return DictFilter.not_none({
            'title': self.title.serialize() if self.title else None,
            'properties': self.properties.serialize() if self.properties else None,
        })


@dataclass
class QueryDatabase(PaginatedRequestBuilder[PageData]):
    data_element_type = PageData
    id: UUID
    filter: Filter = None
    sort: list[Sort] = None
    page_size: int = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'databases/{self.id}/query')

    def get_body(self) -> Any:
        return DictFilter.truthy({
            'filter': self.filter.serialize() if self.filter else None,
            'sorts': [s.serialize() for s in self.sort] if self.sort else None,
        })
