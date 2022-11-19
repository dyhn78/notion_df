from __future__ import annotations as __annotations

from abc import abstractmethod, ABC, ABCMeta
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from typing import Optional, Any


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
    def to_dict(self) -> dict[str, Any]: ...


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


@dataclass
class Emoji(Dictable):
    value: str

    def to_dict(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }


@dataclass
class File(Dictable, metaclass=ABCMeta):
    pass


@dataclass
class InternalFile(File):
    url: str
    expiry_time: datetime

    def to_dict(self):
        return {
            "type": "file",
            "file": {
                "url": self.url,
                "expiry_time": self.expiry_time.isoformat()  # TODO: check Notion time format
            }
        }


@dataclass
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


class Color(Enum):
    default = 'default'
    gray = 'gray'
    brown = 'brown'
    orange = 'orange'
    yellow = 'yellow'
    green = 'green'
    blue = 'blue'
    purple = 'purple'
    pink = 'pink'
    red = 'red'
    gray_background = 'gray_background'
    brown_background = 'brown_background'
    orange_background = 'orange_background'
    yellow_background = 'yellow_background'
    green_background = 'green_background'
    blue_background = 'blue_background'
    purple_background = 'purple_background'
    pink_background = 'pink_background'
    red_background = 'red_background'


@dataclass
class Annotations(Dictable):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: Color | str = Color.default

    def to_dict(self):
        return {
            'bold': self.bold,
            'italic': self.italic,
            'strikethrough': self.strikethrough,
            'underline': self.underline,
            'code': self.code,
            'color': Color(self.color).value
        }


class RichText(Dictable, metaclass=ABCMeta):
    def __init__(self,  annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        self.plain_text = plain_text
        self.href = href
        self.annotations = annotations


@dataclass
class _RichTextDefault:
    annotations: Optional[Annotations] = None
    plain_text: Optional[str] = None
    href: Optional[str] = None


class Text(RichText):
    def __init__(self, content: str, link: Optional[str] = None,
                 annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.content = content
        self.link = link

    def to_dict(self):
        return {
            'annotations': self.annotations,
            'type': 'text',
            'text': {
                'content': self.content,
                'link': {
                    'type': 'url',
                    'url': self.link
                } if self.link else None
            }
        }


class User(Dictable):
    ...


class UserMention(RichText):
    def __init__(self, user: User, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.user = user

    def to_dict(self) -> dict[str, Any]:
        return {
            'annotations': self.annotations,
            'type': 'user',
            'user': self.user.to_dict()
        }


class PageMention(RichText):
    def __init__(self, page_id: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.page_id = page_id

    def to_dict(self) -> dict[str, Any]:
        return {
            'annotations': self.annotations,
            'type': 'page',
            'user': self.page_id
        }


class DatabaseMention(RichText):
    def __init__(self, database_id: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.database_id = database_id

    def to_dict(self) -> dict[str, Any]:
        return {
            'annotations': self.annotations,
            'type': 'database',
            'user': self.database_id
        }
