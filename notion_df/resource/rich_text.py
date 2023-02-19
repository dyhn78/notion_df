from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Optional, Any, Literal, final, Final

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import Annotations, DateRange, UUID
from notion_df.util.misc import dict_filter_truthy


@set_master
class RichText(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/rich-text
    annotations: Optional[Annotations]
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Optional[str]
    """read-only. will be ignored in requests."""
    href: Optional[str]
    """read-only. will be ignored in requests."""

    @final
    def plain_serialize(self) -> dict[str, Any]:
        return self._plain_serialize_main() | self._plain_serialize_defaults()

    @abstractmethod
    def _plain_serialize_main(self) -> dict[str, Any]:
        pass

    @final
    def _plain_serialize_defaults(self) -> dict[str, Any]:
        return dict_filter_truthy({
            'annotations': self.annotations,
            'plain_text': self.plain_text,
            'href': self.href,
        })


@dataclass
class Text(RichText, metaclass=ABCMeta):
    content: str
    link: str
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_main(self) -> dict[str, Any]:
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
class Equation(RichText):
    expression: str
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'expression': self.expression
        }


class Mention(RichText):
    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'type': 'mention',
            'mention': self._plain_serialize_target()
        }

    @abstractmethod
    def _plain_serialize_target(self) -> dict[str, Any]:
        pass


@dataclass
class UserMention(Mention):
    user_id: UUID
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'user',
            'user': {
                'object': 'user',
                'id': self.user_id
            }
        }


@dataclass
class PageMention(Mention):
    page_id: UUID
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'page',
            'user': self.page_id
        }


@dataclass
class DatabaseMention(Mention):
    database_id: UUID
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'database',
            'user': self.database_id
        }


@dataclass
class DateMention(Mention):
    date: DateRange
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'date',
            'date': self.date
        }


@dataclass
class TemplateDateMention(Mention):
    template_mention_date: Literal["today", "now"]
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_date',
            'template_mention_date': self.template_mention_date
        }


@dataclass
class _TemplateUserMention(Mention):
    template_mention_user = 'me'
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'template_mention_user',
            'template_mention_user': self.template_mention_user
        }


@dataclass
class _LinkPreviewMention(Mention):
    """https://developers.notion.com/reference/rich-text#link-preview-mentions"""
    url: str
    # ---
    annotations: Optional[Annotations] = None
    """
    * set `None` (the default value) to leave it unchanged.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""
    href: Final[Optional[str]] = None
    """read-only. will be ignored in requests."""

    def _plain_serialize_target(self) -> dict[str, Any]:
        return {
            'type': 'equation',
            'url': self.url
        }
