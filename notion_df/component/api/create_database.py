from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from typing_extensions import Self

from notion_df.component.api import RequestForm, ResponseForm, RequestSettings
from notion_df.component.common import RichText, Emoji, File
from notion_df.component.schema import PropertySchema
from notion_df.util.parser import parse_datetime


class CreateDatabaseResponseForm(ResponseForm):
    def __init__(self, data: dict[str, Any]):
        self.id = data['id']
        self.created_time = parse_datetime(data['created_time'])
        self.icon = ...  # TODO: first implement Dictable.deserialize()

        self.parent_id_type = data['parent']['type']
        self.parent_id = data['parent'][self.parent_id_type]
        self.archived = data['archived']

    @classmethod
    def parse(cls, response: dict[str, Any]) -> Self:
        pass


@dataclass
class CreateDatabaseRequestForm(RequestForm[CreateDatabaseResponseForm]):
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
