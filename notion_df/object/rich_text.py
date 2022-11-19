from __future__ import annotations as __

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, Literal, Callable

from notion_df.object.misc import Annotations
from notion_df.property.date_property import DatePropertyValue
from notion_df.utils.mixin import Dictable


@dataclass(init=False)
class RichText(Dictable, metaclass=ABCMeta):
    ...


@dataclass
class _RichTextDefault(Dictable, metaclass=ABCMeta):
    annotations: Optional[Annotations] = None
    plain_text: Optional[str] = None
    href: Optional[str] = None

    def __init_subclass__(cls: type[RichText], **kwargs):
        print('YEAH')
        to_dict = cls.to_dict

        def wrapper(self: _RichTextDefault):
            _default_to_dict = {'annotations': self.annotations.to_dict()} if self.annotations else {}
            return to_dict(self) | _default_to_dict

        cls.to_dict = wrapper


@dataclass
class _Text(RichText):
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
class Text(_RichTextDefault, _Text):
    pass


class Equation(RichText):
    def __init__(self, expression: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        """https://developers.notion.com/reference/rich-text#equation-objects"""
        super().__init__(annotations, plain_text, href)
        self.expression = expression

    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'type': 'equation',
            'expression': self.expression
        }


class Mention(RichText):
    def to_dict(self) -> dict[str, Any]:
        return super().to_dict() | {
            'type': 'mention',
            'mention': self._mention_to_dict()
        }

    @abstractmethod
    def _mention_to_dict(self) -> dict[str, Any]:
        pass


class UserMention(Mention):
    def __init__(self, user_id: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.user_id = user_id

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'user',
            'user': {
                'object': 'user',
                'id': self.user_id
            }
        }


class PageMention(Mention):
    def __init__(self, page_id: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.page_id = page_id

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'page',
            'user': self.page_id
        }


class DatabaseMention(Mention):
    def __init__(self, database_id: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.database_id = database_id

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'database',
            'user': self.database_id
        }


class DateMention(Mention):
    def __init__(self, value: DatePropertyValue,
                 annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.value = value

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'date',
            'date': self.value.to_dict()
        }


class TemplateDateMention(Mention):
    def __init__(self, template_mention_date: Literal["today", "now"],
                 annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.template_mention_date = template_mention_date

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_date',
            'template_mention_date': self.template_mention_date
        }


class TemplateUserMention(Mention):
    def __init__(self, template_mention_user: Literal["me"],
                 annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        super().__init__(annotations, plain_text, href)
        self.template_mention_user = template_mention_user

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_user',
            'template_mention_user': self.template_mention_user
        }


class LinkPreviewMention(Mention):
    def __init__(self, url: str, annotations: Optional[Annotations] = None,
                 plain_text: Optional[str] = None, href: Optional[str] = None):
        """https://developers.notion.com/reference/rich-text#link-preview-mentions"""
        super().__init__(annotations, plain_text, href)
        self.url = url

    def _mention_to_dict(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'url': self.url
        }
