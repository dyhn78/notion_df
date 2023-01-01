from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, Literal, final

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import Annotations, DateRange, UUID


@set_master
@dataclass(init=False)
class RichText(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/rich-text
    @final
    def plain_serialize(self) -> dict[str, Any]:
        serialized = self._plain_serialize_value()
        if self.annotations:
            serialized['annotations'] = self.annotations
        return serialized

    @abstractmethod
    def _plain_serialize_value(self) -> dict[str, Any]:
        pass


@dataclass
class _RichTextDefault(Deserializable, metaclass=ABCMeta):
    # this is a helper class we need to put common, default, annotation-like variables
    #  AFTER subclass-specific, important ones.
    annotations: Optional[Annotations] = None
    """
    * set as `None` (the default value) to leave it unchanged.
    * set as `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Optional[str] = None
    """read-only. will be ignored in requests."""
    href: Optional[str] = None
    """read-only. will be ignored in requests."""


@dataclass
class _Text(RichText, metaclass=ABCMeta):
    content: str
    link: str

    def _plain_serialize_value(self) -> dict[str, Any]:
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
class _Equation(RichText):
    expression: str

    def _plain_serialize_value(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'expression': self.expression
        }


class Mention(RichText):
    def _plain_serialize_value(self) -> dict[str, Any]:
        return {
            'type': 'mention',
            'mention': self._plain_serialize_inner_value()
        }

    @abstractmethod
    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        pass


@dataclass
class _UserMention(Mention):
    user_id: UUID

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'user',
            'user': {
                'object': 'user',
                'id': self.user_id
            }
        }


@dataclass
class _PageMention(Mention):
    page_id: UUID

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'page',
            'user': self.page_id
        }


@dataclass
class _DatabaseMention(Mention):
    database_id: UUID

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'database',
            'user': self.database_id
        }


@dataclass
class _DateMention(Mention):
    date: DateRange

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'date',
            'date': self.date
        }


@dataclass
class _TemplateDateMention(Mention):
    template_mention_date: Literal["today", "now"]

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_date',
            'template_mention_date': self.template_mention_date
        }


@dataclass
class _TemplateUserMention(Mention):
    template_mention_user = 'me'

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_user',
            'template_mention_user': self.template_mention_user
        }


@dataclass
class _LinkPreviewMention(Mention):
    """https://developers.notion.com/reference/rich-text#link-preview-mentions"""
    url: str

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'url': self.url
        }


@dataclass
class Text(_RichTextDefault, _Text):
    pass


@dataclass
class Equation(_RichTextDefault, _Equation):
    pass


@dataclass
class UserMention(_RichTextDefault, _UserMention):
    pass


@dataclass
class PageMention(_RichTextDefault, _PageMention):
    pass


@dataclass
class DatabaseMention(_RichTextDefault, _DatabaseMention):
    pass


@dataclass
class DateMention(_RichTextDefault, _DateMention):
    pass


@dataclass
class TemplateDateMention(_RichTextDefault, _TemplateDateMention):
    pass


@dataclass
class TemplateUserMention(_RichTextDefault, _TemplateUserMention):
    pass


@dataclass
class LinkPreviewMention(_RichTextDefault, _LinkPreviewMention):
    pass
