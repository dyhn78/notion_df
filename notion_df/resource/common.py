from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from datetime import datetime
from typing import Optional, Any, Literal, ClassVar, Final

from notion_df.resource.core import TypedResource, Resource
from notion_df.util.collection import StrEnum


class RichText(TypedResource, metaclass=ABCMeta):
    # https://developers.notion.com/reference/rich-text
    ...


@dataclass
class _RichTextDefault(TypedResource, metaclass=ABCMeta):
    # this is a helper class we need to put common, default, annotation-like variables
    #  AFTER subclass-specific, important ones.
    annotations: Optional[Annotations] = None
    """
    * set as `None` (the default value) to leave it unchanged.
    * set as `Annotations()` to remove the annotations and make a plain text.
    """

    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def serialize_plain(self) -> dict[str, Any]:
        return {'annotations': self.annotations} if self.annotations else {}


@dataclass
class _Text(RichText, metaclass=ABCMeta):
    content: str
    link: str

    def serialize_plain(self):
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
class Text(_RichTextDefault, _Text):
    pass


@dataclass
class _Equation(RichText):
    expression: str

    def serialize_plain(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'expression': self.expression
        }


@dataclass
class Equation(_RichTextDefault, _Equation):
    pass


class Mention(RichText):
    def serialize_plain(self) -> dict[str, Any]:
        return {
            'type': 'mention',
            'mention': self._serialize_inner_value()
        }

    @abstractmethod
    def _serialize_inner_value(self) -> dict[str, Any]:
        pass


@dataclass
class _UserMention(Mention):
    user_id: str

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'user',
            'user': {
                'object': 'user',
                'id': self.user_id
            }
        }


@dataclass
class UserMention(_RichTextDefault, _UserMention):
    pass


@dataclass
class _PageMention(Mention):
    page_id: str

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'page',
            'user': self.page_id
        }


@dataclass
class PageMention(_RichTextDefault, _PageMention):
    pass


@dataclass
class _DatabaseMention(Mention):
    database_id: str

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'database',
            'user': self.database_id
        }


@dataclass
class DatabaseMention(_RichTextDefault, _DatabaseMention):
    pass


@dataclass
class _DateMention(Mention):
    date: DateValue

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'date',
            'date': self.date
        }


@dataclass
class DateMention(_RichTextDefault, _DateMention):
    pass


@dataclass
class _TemplateDateMention(Mention):
    template_mention_date: Literal["today", "now"]

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_date',
            'template_mention_date': self.template_mention_date
        }


@dataclass
class TemplateDateMention(_RichTextDefault, _TemplateDateMention):
    pass


@dataclass
class _TemplateUserMention(Mention):
    template_mention_user: Literal["me"]

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_user',
            'template_mention_user': self.template_mention_user
        }


@dataclass
class TemplateUserMention(_RichTextDefault, _TemplateUserMention):
    pass


@dataclass
class _LinkPreviewMention(Mention):
    """https://developers.notion.com/reference/rich-text#link-preview-mentions"""
    url: str

    def _serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'url': self.url
        }


@dataclass
class LinkPreviewMention(_RichTextDefault, _LinkPreviewMention):
    pass


class Icon(TypedResource, metaclass=ABCMeta):
    pass


@dataclass
class Emoji(Icon):
    # https://developers.notion.com/reference/emoji-object
    value: str
    TYPE: ClassVar = 'emoji'

    def serialize_plain(self):
        return {
            "type": "emoji",
            "emoji": self.value
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

    def serialize_plain(self) -> dict[str, str]:
        return {
            'bold': self.bold,
            'italic': self.italic,
            'strikethrough': self.strikethrough,
            'underline': self.underline,
            'code': self.code,
            'color': self.color
        }


@dataclass
class DateValue(Resource):
    # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
    start: datetime
    end: datetime

    def serialize_plain(self):
        return {
            'start': self.start,
            'end': self.end,
        }
