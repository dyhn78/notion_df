from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Literal, ClassVar

from notion_df.resource.property import DatePropertyValue
from notion_df.resource.resource import Resource
from notion_df.util.collection import StrEnum


class RichText(Resource, metaclass=ABCMeta):
    ...


@dataclass
class _RichText(Resource, metaclass=ABCMeta):
    annotations: Optional[Annotations] = None
    plain_text: Optional[str] = None
    href: Optional[str] = None

    def __init_subclass__(cls: type[RichText], **kwargs):
        super().__init_subclass__(**kwargs)
        to_dict = cls.to_dict

        def wrapper(self: _RichText):
            _default_to_dict = {'annotations': self.annotations.to_dict()} if self.annotations else {}
            return to_dict(self) | _default_to_dict

        cls.to_dict = wrapper


@dataclass
class _Text(RichText, metaclass=ABCMeta):
    content: str
    link: str

    def to_dict(self):
        return {
            'type': 'text',
            'text': {
                'content': self.content,
                'link': {
                    'type': 'url',
                    'url': self.link
                } if self.link else None
            }
        }


@dataclass
class Text(_RichText, _Text):
    pass


@dataclass
class _Equation(RichText):
    expression: str

    def to_dict(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'expression': self.expression
        }


@dataclass
class Equation(_RichText, _Equation):
    pass


class Mention(RichText):
    def to_dict(self) -> dict[str, Any]:
        return {
            'type': 'mention',
            'mention': self._mention_to_dict()
        }

    @abstractmethod
    def _mention_to_dict(self) -> dict[str, Any]:
        pass


@dataclass
class _UserMention(Mention):
    user_id: str

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'user',
            'user': {
                'object': 'user',
                'id': self.user_id
            }
        }


@dataclass
class UserMention(_RichText, _UserMention):
    pass


@dataclass
class _PageMention(Mention):
    page_id: str

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'page',
            'user': self.page_id
        }


@dataclass
class PageMention(_RichText, _PageMention):
    pass


@dataclass
class _DatabaseMention(Mention):
    database_id: str

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'database',
            'user': self.database_id
        }


@dataclass
class DatabaseMention(_RichText, _DatabaseMention):
    pass


@dataclass
class _DateMention(Mention):
    date: DatePropertyValue

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'date',
            'date': self.date.to_dict()
        }


@dataclass
class DateMention(_RichText, _DateMention):
    pass


@dataclass
class _TemplateDateMention(Mention):
    template_mention_date: Literal["today", "now"]

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_date',
            'template_mention_date': self.template_mention_date
        }


@dataclass
class TemplateDateMention(_RichText, _TemplateDateMention):
    pass


@dataclass
class _TemplateUserMention(Mention):
    template_mention_user: Literal["me"]

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_user',
            'template_mention_user': self.template_mention_user
        }


@dataclass
class TemplateUserMention(_RichText, _TemplateUserMention):
    pass


@dataclass
class _LinkPreviewMention(Mention):
    """https://developers.notion.com/reference/rich-text#link-preview-mentions"""
    url: str

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'url': self.url
        }


@dataclass
class LinkPreviewMention(_RichText, _LinkPreviewMention):
    pass


@dataclass
class Emoji(Resource):
    value: str
    TYPE: ClassVar = 'emoji'

    def to_dict(self):
        return {
            "type": "emoji",
            "emoji": self.value
        }

    @classmethod
    def from_dict(cls, d: dict) -> Emoji:
        return cls(d['emoji'])


@dataclass
class File(Resource, metaclass=ABCMeta):
    TYPE: ClassVar = 'file'


@dataclass
class InternalFile(File):
    url: str
    expiry_time: datetime

    def to_dict(self):
        return {
            "type": "file",
            "file": {
                "url": self.url,
                "expiry_time": self.expiry_time.isoformat()
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


class Color(StrEnum):
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
class Annotations(Resource):
    bold: bool = False
    italic: bool = False
    strikethrough: bool = False
    underline: bool = False
    code: bool = False
    color: Color | str = Color.default

    def to_dict(self) -> dict[str, str]:
        return {
            'bold': self.bold,
            'italic': self.italic,
            'strikethrough': self.strikethrough,
            'underline': self.underline,
            'code': self.code,
            'color': Color(self.color).value
        }