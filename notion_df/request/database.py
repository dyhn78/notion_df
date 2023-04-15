from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from typing_extensions import Self

from notion_df.object.core import Deserializable
from notion_df.object.database import DatabaseProperty
from notion_df.object.file import File, ExternalFile
from notion_df.object.filter import Filter
from notion_df.object.misc import Icon, UUID
from notion_df.object.parent import Parent
from notion_df.object.rich_text import RichText
from notion_df.object.sort import Sort
from notion_df.request.core import Request, RequestSettings, Version, Method, PaginatedRequest
from notion_df.request.page import ResponsePage
from notion_df.util.collection import DictFilter


@dataclass
class ResponseDatabase(Deserializable):
    # TODO: configure Property -> DatabaseProperty 1:1 mapping, from Property's side.
    #  access this mapping from Property (NOT ResponseDatabase), the base class.
    #  Property.from_schema(schema: DatabaseProperty) -> Property
    #  then, make Page or Database utilize it,
    #  so that they could autoconfigure itself and its children with the retrieved data.
    id: UUID
    parent: Parent
    created_time: datetime
    last_edited_time: datetime
    icon: Icon
    cover: ExternalFile
    url: str
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    archived: bool
    is_inline: bool

    @classmethod
    def deserialize(cls, response_data: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(response_data)


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
