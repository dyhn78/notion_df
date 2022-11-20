from __future__ import annotations

from abc import abstractmethod, ABCMeta
from dataclasses import dataclass

from notion_df.form.common import RichText, Emoji, File
from notion_df.utils.mixin import Dictable


class RequestBuilder:
    ENDPOINT = "https://api.notion.com/v1/"

    @classmethod
    @abstractmethod
    def _get_entrypoint(cls):
        pass


class CreateDatabase(RequestBuilder):
    @classmethod
    @abstractmethod
    def _get_entrypoint(cls):
        return "https://api.notion.com/v1/databases/"


class RequestParams(Dictable, metaclass=ABCMeta):
    ...


@dataclass
class CreateDatabaseParams(RequestParams):
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


class PropertySchema(Dictable, metaclass=ABCMeta):
    ...
