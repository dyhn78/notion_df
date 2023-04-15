from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field, fields, Field
from datetime import datetime
from functools import cache
from typing import Any, Literal, Union, cast, Optional

from _decimal import Decimal
from typing_extensions import Self

from notion_df.response.core import Deserializable, resolve_by_keychain
from notion_df.response.file import ExternalFile, File
from notion_df.response.misc import UUID, Icon, DateRange, SelectOption, RollupFunction
from notion_df.response.parent import Parent
from notion_df.response.rich_text import RichText
from notion_df.response.user import User
from notion_df.util.collection import FinalClassDict


@dataclass
class ResponsePage(Deserializable):
    id: UUID
    parent: Parent
    created_time: datetime
    last_edited_time: datetime
    created_by: User
    last_edited_by: User
    icon: Icon
    cover: ExternalFile
    url: str
    title: list[RichText]
    properties: dict[str, PageProperty] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    archived: bool
    is_inline: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "page",
            "id": self.id,
            "created_time": self.created_by,
            "last_edited_time": self.last_edited_by,
            "created_by": self.created_by,
            "last_edited_by": self.last_edited_by,
            "cover": self.cover,
            "icon": self.icon,
            "parent": self.parent,
            "archived": False,
            "properties": self.properties,
            "url": self.url,
        }


@resolve_by_keychain('object')
class BaseResponsePageProperty(Deserializable, metaclass=ABCMeta):
    pass


@dataclass
class ResponsePageProperty(BaseResponsePageProperty):
    property_item: PageProperty

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "property_item",
            "id": "kjPO",
            **self.property_item
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_value_presets) -> dict[str, Any]:
        return {'property_item': serialized}


@dataclass
class ResponsePagePropertyList(BaseResponsePageProperty):
    property_item: PageProperty
    results: list[ResponsePageProperty]
    next_cursor: Optional[str]
    has_more: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "list",
            "results": self.results,
            "next_cursor": self.next_cursor,
            "has_more": self.has_more,
            "property_item": self.property_item,
            "type": "property_item"
        }


@dataclass
class PageProperty(Deserializable, metaclass=ABCMeta):
    """
    represents two types of data structure.

    - partial page property - user side
    - page property - server side

    page property has additional fields, `name` and `id`. these are hidden from __init__() to prevent confusion.

    https://developers.notion.com/reference/page-property-values
    """
    name: str = field(init=False)
    id: str = field(init=False)

    @classmethod
    @cache
    def get_type(cls) -> str:
        """by default, return the first subclass-specific field's name.
        you should override this if the class definition does not comply the assumption."""
        return cast(Field, fields(cls)[len(fields(PageProperty))]).name

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        page_property_registry[cls.get_type()] = cls

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_value_presets) -> Self:
        return super()._plain_deserialize(serialized, type=serialized['type'])

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != PageProperty:
            return super().deserialize(serialized)
        page_property_cls = page_property_registry[serialized['type']]
        return page_property_cls.deserialize(serialized)


page_property_registry = FinalClassDict[str, type[PageProperty]]()


@dataclass
class CheckboxPageProperty(PageProperty):
    checkbox: bool


@dataclass
class CreatedByPageProperty(PageProperty):
    created_by: User


@dataclass
class LastEditedByPageProperty(PageProperty):
    last_edited_by: User


@dataclass
class PeoplePageProperty(PageProperty):
    people: list[User]


@dataclass
class CreatedTimePageProperty(PageProperty):
    created_time: datetime


@dataclass
class LastEditedTimePageProperty(PageProperty):
    last_edited_time: datetime


@dataclass
class DatePageProperty(PageProperty):
    date: DateRange


@dataclass
class EmailPageProperty(PageProperty):
    email: str


@dataclass
class PhoneNumberPageProperty(PageProperty):
    phone_number: str


@dataclass
class URLPageProperty(PageProperty):
    url: str


@dataclass
class FilesPageProperty(PageProperty):
    files: list[File]


@dataclass
class FormulaPageProperty(PageProperty):
    value_type: Literal['boolean', 'date', 'number', 'string']
    value: Union[bool, datetime, int, Decimal, str]

    @classmethod
    def get_type(cls) -> str:
        return 'formula'

    def _plain_serialize(self) -> Any:
        return {**super()._plain_serialize(),
                'formula': {'type': self.value_type, self.value_type: self.value}}


@dataclass
class MultiSelectPageProperty(PageProperty):
    multi_select: list[SelectOption]


@dataclass
class NumberPageProperty(PageProperty):
    number: Union[int, Decimal]


@dataclass
class RelationPageProperty(PageProperty):
    page_ids: list[UUID]
    has_more: bool = field(init=False)

    @classmethod
    def get_type(cls) -> str:
        return 'relation'

    def _plain_serialize(self) -> Any:
        return {**super()._plain_serialize(),
                'relation': [{'id': page_id} for page_id in self.page_ids]}

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_value_presets) -> Self:
        return cls._plain_deserialize(serialized,
                                      page_ids=[UUID(page['id']) for page in serialized['relation']],
                                      has_more=serialized['has_more'])


@dataclass
class RollupPageProperty(PageProperty):
    # TODO: dynamically link rollup values to basic values (for example, RelationPageProperty, DatePageProperty)
    function: RollupFunction
    value_type: Literal['array', 'date', 'incomplete', 'number', 'unsupported']
    value: Any

    @classmethod
    def get_type(cls) -> str:
        return 'rollup'

    def _plain_serialize(self) -> Any:
        return {**super()._plain_serialize(),
                'rollup': {'function': self.function, 'type': self.value_type, self.value_type: self.value}}

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_value_presets) -> Self:
        return super()._plain_deserialize(serialized, value_type=serialized['rollup']['type'])


@dataclass
class RichTextPageProperty(PageProperty):
    rich_text: list[RichText]


@dataclass
class TitlePageProperty(PageProperty):
    title: list[RichText]


@dataclass
class SelectPageProperty(PageProperty):
    select: SelectOption


@dataclass
class StatusPageProperty(PageProperty):
    status: SelectOption
