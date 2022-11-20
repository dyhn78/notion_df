from __future__ import annotations

import os
from abc import abstractmethod
from dataclasses import dataclass

import requests

from notion_df.form.common import RichText, Emoji, File
from notion_df.form.request import RequestBuilder
from notion_df.form.schema import PropertySchema
from notion_df.util.mixin import Dictable

NOTION_API_KEY = os.getenv('NOTION_API_KEY')

headers = {
    'Authorization': f"Bearer {NOTION_API_KEY}",
    'Notion-Version': '2022-06-28',
}

json_data = {
    'x': 'y',
}

response = requests.post('https://api.notion.com/v1/databases/', headers=headers, json=json_data)


class CreateDatabase(RequestBuilder):
    @classmethod
    @abstractmethod
    def _get_entrypoint(cls):
        return "https://api.notion.com/v1/databases/"

    def request(self):  # TODO
        url = 'https://api.notion.com/v1/databases/'
        response = requests.post(url, data=data, headers=self.headers)


@dataclass
class CreateDatabaseParams(Dictable):
    parent_id: str
    icon: Emoji | File
    cover: File
    title: list[RichText]
    properties: dict[str, PropertySchema]

    def to_dict(self) -> dict:
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
