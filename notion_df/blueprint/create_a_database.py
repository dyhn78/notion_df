from __future__ import annotations
from abc import abstractmethod, ABC, ABCMeta
from dataclasses import dataclass
from datetime import datetime


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


class Dictable(ABC):
    @abstractmethod
    def to_dict(self) -> dict: ...


# class Dictable2(Dictable):
#     @classmethod
#     @abstractmethod
#     def from_dict(cls, value: dict) -> Self: ...


class RequestParams(Dictable, metaclass=ABCMeta):
    ...


@dataclass
class CreateDatabaseParams(RequestParams):
    parent_id: str
    icon: Emoji | File
    cover: File
    title: RichText
    properties: dict[str, PropertySchema]

    def to_dict(self) -> dict:
        return {
            "parent": {
                "type": "page_id",
                "page_id": self.parent_id
            },
            "icon": self.icon.to_dict(),
            "cover": self.cover.to_dict(),
            "title": self.title.to_dict(),
            "properties": {
                name: schema.to_dict() for name, schema in self.properties.items()
            }
        }


class RichText(Dictable, metaclass=ABCMeta):
    ...


class Emoji(Dictable):
    value: str

    def to_dict(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }


class File(Dictable, metaclass=ABCMeta):
    ...


class InternalFile(File):
    url: str
    expiry_time: datetime

    def to_dict(self):
        return {
            "type": "file",
            "file": {
                "url": self.url,
                # TODO: check Notion time format
                "expiry_time": self.expiry_time.isoformat()
            }
        }


class ExternalFile(File):
    url: str

    def to_dict(self):
        return {
            "type": "external",
            "external": {
                "url": self.url
            }
        }


class PropertySchema(Dictable, metaclass=ABCMeta):
    ...
