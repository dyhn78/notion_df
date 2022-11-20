from __future__ import annotations

from abc import abstractmethod
from dataclasses import dataclass

from notion_df.form.common import RichText, Emoji, File
from notion_df.form.request import RequestBuilder
from notion_df.form.schema import PropertySchema
from notion_df.util.mixin import Dictable


class CreateDatabase(RequestBuilder):
    @classmethod
    @abstractmethod
    def _get_entrypoint(cls):
        return "https://api.notion.com/v1/databases/"


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
