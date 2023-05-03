from __future__ import annotations

from _decimal import Decimal
from abc import ABCMeta
from dataclasses import dataclass, field, fields, Field
from datetime import datetime
from functools import cache
from typing import Any, Literal, Union, cast, final

from typing_extensions import Self

from notion_df.core.response import Response
from notion_df.object.common import UUID, DateRange, SelectOption, Icon, Properties, Property
from notion_df.object.constant import RollupFunction
from notion_df.object.file import File, ExternalFile
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.object.user import User
from notion_df.util.collection import FinalClassDict

page_property_registry: FinalClassDict[str, type[PageProperty]] = FinalClassDict()


@dataclass
class PageResponse(Response):
    id: UUID
    parent: ParentInfo
    created_time: datetime
    last_edited_time: datetime
    created_by: User
    last_edited_by: User
    archived: bool
    icon: Icon
    cover: ExternalFile
    url: str
    properties: PageProperties

    @classmethod
    def _deserialize_this(cls, response_data: dict[str, Any]) -> Self:
        properties = {}
        for prop_name, prop_serialized in response_data['properties'].items():
            prop = PageProperty.deserialize(prop_serialized)
            prop.name = prop_name
            properties[prop_name] = prop
        return cls._deserialize_from_dict(response_data, properties=properties)


@dataclass
class PageProperty(Property, metaclass=ABCMeta):
    """https://developers.notion.com/reference/page-property-values"""

    @classmethod
    @cache
    def get_typename(cls) -> str:
        """by default, return the first subclass-specific field's name.
        you should override this if the class definition does not comply the assumption."""
        return cast(Field, fields(cls)[len(fields(PageProperty))]).name

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        dataclass(cls)
        page_property_registry[cls.get_typename()] = cls

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls == PageProperty:
            subclass = page_property_registry[serialized['type']]
            return subclass.deserialize(serialized)
        return cls._deserialize_this(serialized)


PageProperties = Properties[PageProperty]


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
    def get_typename(cls) -> str:
        return 'formula'

    def serialize(self) -> Any:
        return {'formula': {'type': self.value_type, self.value_type: self.value}}


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
    def get_typename(cls) -> str:
        return 'relation'

    def serialize(self) -> Any:
        return {'relation': [{'id': page_id} for page_id in self.page_ids]}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls(page_ids=[UUID(page['id']) for page in serialized['relation']])
        self.has_more = serialized['has_more']
        return self


@dataclass
class RollupPageProperty(PageProperty):
    # TODO: dynamically link rollup values to basic values (for example, RelationPageProperty, DatePageProperty)
    function: RollupFunction
    value_type: Literal['array', 'date', 'incomplete', 'number', 'unsupported']
    value: Any

    @classmethod
    def get_typename(cls) -> str:
        return 'rollup'

    def serialize(self) -> Any:
        return {'rollup': {'function': self.function, 'type': self.value_type, self.value_type: self.value}}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        rollup = serialized['rollup']
        value_type = rollup['type']
        return cls(function=rollup['function'], value_type=value_type, value=rollup[value_type])


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
