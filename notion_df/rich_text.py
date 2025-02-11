from __future__ import annotations as _

import functools
from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Optional, Any, Literal, Iterable, cast
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import DualSerializable, deserialize, serialize
from notion_df.entity import Page, Database
from notion_df.misc import DateRange, Annotations
from notion_df.core.collection import FinalDict
from notion_df.user import User

span_registry: FinalDict[tuple[str, ...], type[Span]] = FinalDict()


@dataclass
class Span(DualSerializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/rich-text
    annotations = None  # actual type: Optional[Annotations]
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """
    plain_text: str = field(init=False, repr=False)
    href: str = field(init=False, repr=False)

    def __post_init__(self):
        self.plain_text = ""
        self.href = ""

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if (typename := cls.get_typename()) and typename != cast(
            cls, super(cls, cls)
        ).get_typename():
            span_registry[cls.get_typename()] = cls

        _serialize = cls.serialize
        _deserialize_this = cls._deserialize_this

        @functools.wraps(_serialize)
        def _serialize_wrapped(self: Span):
            raw = _serialize(self)
            if self.annotations is not None:
                # noinspection PyTestUnpassedFixture
                raw["annotations"] = self.annotations.serialize()
            return raw

        @functools.wraps(_deserialize_this)
        def _deserialize_this_wrapped(raw: dict[str, Any]):
            self = _deserialize_this(raw)
            self.annotations = Annotations.deserialize(raw["annotations"])
            self.plain_text = raw["plain_text"]
            self.href = raw["href"]
            return self

        setattr(cls, "serialize", _serialize_wrapped)
        setattr(cls, "_deserialize_this", _deserialize_this_wrapped)

    @classmethod
    @abstractmethod
    def get_typename(cls) -> tuple[str, ...]:
        return ()

    @classmethod
    def _deserialize_subclass(cls, raw: dict[str, Any]) -> Self:
        def get_typename(_raw: dict[str, Any]) -> tuple[str, ...]:
            if "type" in _raw:
                typename = _raw["type"]
                return (typename,) + get_typename(_raw[typename])
            return ()

        #  TODO: remove this temporary hack [[ (ex) KeyError: ('mention', 'user', 'person') -> ('mention', 'user') ]]
        subclass = span_registry[get_typename(raw)[:2]]
        return subclass.deserialize(raw)

    def __repr__(self):
        return self._repr_non_default_fields()


class RichText(list[Span], DualSerializable):
    def __init__(self, spans: Iterable[Span] = ()):
        super().__init__(spans)

    @property
    def plain_text(self) -> str:
        return "".join(span.plain_text for span in self)

    @classmethod
    def from_plain_text(cls, plain_text: Optional[str]) -> Self:
        """TODO integrate to __init__"""
        return cls([TextSpan(plain_text)]) if plain_text else cls()

    def serialize(self) -> Any:
        return serialize(list(self))

    @classmethod
    def _deserialize_this(cls, raw: Any) -> Self:
        return cls(deserialize(list[Span], raw))


@dataclass
class TextSpan(Span):
    content: str
    """max_length: 2000"""
    link: Optional[str] = field(default=None)
    # ---
    annotations: Optional[Annotations] = field(default=None)
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def __post_init__(self) -> None:
        super().__post_init__()
        if not self.plain_text:
            self.plain_text = self.content

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "text",
            "text": {
                "content": self.content,
                "link": {"type": "url", "url": self.link} if self.link else None,
            },
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return ("text",)

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        link_item = raw["text"]["link"]
        link = link_item["url"] if link_item else None
        return cls(raw["text"]["content"], link)


@dataclass
class Equation(Span):
    expression: str
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {"type": "equation", "expression": self.expression}

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return ("equation",)

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["expression"])


@dataclass
class UserMention(Span):
    user: User
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {
                "type": "user",
                "user": {"object": "user", "id": str(self.user.id)},
            },
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "user"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["mention"]["user"]["id"])


@dataclass
class PageMention(Span):
    page: Page
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {"type": "page", "page": {"id": str(self.page.id)}},
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "page"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["mention"]["page"]["id"])


@dataclass
class DatabaseMention(Span):
    database: Database
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {"type": "database", "database": {"id": str(self.database.id)}},
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "database"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["mention"]["database"]["id"])


@dataclass
class DateMention(Span):
    date: DateRange
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {"type": "date", "date": self.date.serialize()},
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "date"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["mention"]["date"])


@dataclass
class TemplateDateMention(Span):
    template_mention_date: Literal["today", "now"]
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {
                "type": "template_mention",
                "template_mention": {
                    "type": "template_mention_date",
                    "template_mention_date": self.template_mention_date,
                },
            },
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "template_mention", "template_mention_date"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["mention"]["database"])


@dataclass
class TemplateUserMention(Span):
    template_mention_user = "me"
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {
                "type": "template_mention",
                "template_mention": {
                    "type": "template_mention_user",
                    "template_mention_user": self.template_mention_user,
                },
            },
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "template_mention", "template_mention_user"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls()


@dataclass
class LinkPreviewMention(Span):
    """https://developers.notion.com/reference/rich-text#link-preview-mentions"""

    url: str
    # ---
    annotations: Optional[Annotations] = None
    """
    Note: when updating block texts,
    
    * set `None` (the default value) to retain the current annotations.
    * set `Annotations()` to remove the annotations and make a plain text.
    """

    def serialize(self) -> dict[str, Any]:
        return {
            "type": "mention",
            "mention": {"type": "link_preview", "link_preview": {"url": self.url}},
        }

    @classmethod
    def get_typename(cls) -> tuple[str, ...]:
        return "mention", "link_preview"

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["mention"]["link_preview"]["url"])


# TODO: link_mention
