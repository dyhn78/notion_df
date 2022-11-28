from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import Self

from notion_df.request import Request, Response, RequestSettings
from notion_df.resource.common import RichText, Emoji, File
from notion_df.resource.schema import PropertySchema
from notion_df.util.parser import parse_datetime


class DatabaseResponse(Response):
    def __init__(self, data: dict[str, Any]):
        self.id = data['id']
        self.created_time = parse_datetime(data['created_time'])
        self.icon = ...  # TODO: first implement Resource.deserialize()

        self.parent_id_type = data['parent']['type']
        self.parent_id = data['parent'][self.parent_id_type]
        self.archived = data['archived']

    @classmethod
    def from_raw_data(cls, data: dict[str, Any]) -> Self:
        pass


@dataclass
class CreateDatabaseRequest(Request[DatabaseResponse]):
    """https://developers.notion.com/reference/create-a-database"""
    parent_id: str
    icon: Emoji | File
    cover: File
    title: list[RichText]
    properties: dict[str, PropertySchema]  # TODO: make this a list

    @classmethod
    def get_settings(cls) -> RequestSettings:
        return RequestSettings(
            notion_version='2022-06-28',
            endpoint='https://api.notion.com/v1/databases/',
            method='POST',
        )

    def get_path(self) -> str:
        return ''

    def get_body(self) -> dict:
        return {
            "parent": {
                "type": "page_id",
                "page_id": self.parent_id
            },
            "icon": self.icon.to_dict(),
            "cover": self.cover.to_dict(),
            "title": [rich_text.to_dict() for rich_text in self.title],
            "properties": {name: schema.to_dict() for name, schema in self.properties.items()}
        }
