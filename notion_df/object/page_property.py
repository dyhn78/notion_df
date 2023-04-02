from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from decimal import Decimal
from typing import Any, Union, Literal

from typing_extensions import Self

from notion_df.object.core import Deserializable
from notion_df.object.file import File
from notion_df.object.misc import DateRange, SelectOption, UUID, RollupFunction
from notion_df.object.rich_text import RichText
from notion_df.object.user import User
from notion_df.util.collection import FinalClassDict


@dataclass
class PageProperty(Deserializable, metaclass=ABCMeta):
    """
    represents two types of data structure.

    - partial page property - user side
    - page property - server side

    page property has additional fields, `name` and `id`. these are hidden from __init__() to prevent confusion.

    https://developers.notion.com/reference/page-property-values
    """
    type: str
    name: str = field(init=False)
    id: str = field(init=False)

    @classmethod
    @abstractmethod
    def _eligible_property_types(cls) -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        for property_type in cls._eligible_property_types():
            page_property_by_property_type_dict[property_type] = cls

    @abstractmethod
    def _plain_serialize_type_object(self) -> Any:
        """https://developers.notion.com/reference/page-property-values#type-objects"""
        pass

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            self.type: self._plain_serialize_type_object(),
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars) -> Self:
        self = super()._plain_deserialize(serialized, type=serialized['type'])
        self.name = serialized['name']
        self.id = serialized['id']
        return self

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != PageProperty:
            return super().deserialize(serialized)
        property_type = serialized['type']
        page_property_type = page_property_by_property_type_dict[property_type]
        return page_property_type.deserialize(serialized)


page_property_by_property_type_dict = FinalClassDict[str, type[PageProperty]]()


@dataclass
class CheckboxPageProperty(PageProperty):
    checkbox: bool

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['checkbox']

    def _plain_serialize_type_object(self):
        return self.checkbox


@dataclass
class PersonPageProperty(PageProperty):
    user: User

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['created_by', 'last_edited_by']

    def _plain_serialize_type_object(self) -> Any:
        return self.user


@dataclass
class PeoplePageProperty(PageProperty):
    people: list[User]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['people']

    def _plain_serialize_type_object(self) -> Any:
        return self.people


@dataclass
class SingleDatePageProperty(PageProperty):
    date: datetime

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['created_time', 'last_edited_time']

    def _plain_serialize_type_object(self) -> Any:
        return self.date


@dataclass
class DoubleDatePageProperty(PageProperty):
    date_range: DateRange

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['date']

    def _plain_serialize_type_object(self) -> Any:
        return self.date_range


@dataclass
class StringPageProperty(PageProperty):
    string: str

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['email', 'phone_number', 'url']

    def _plain_serialize_type_object(self) -> Any:
        return self.string


@dataclass
class FilesPageProperty(PageProperty):
    files = list[File]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['files']

    def _plain_serialize_type_object(self) -> Any:
        return self.files


@dataclass
class FormulaPageProperty(PageProperty):
    value_type: Literal['boolean', 'date', 'number', 'string']
    value: Union[bool, datetime, int, Decimal, str]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['formula']

    def _plain_serialize_type_object(self) -> Any:
        return {'type': self.value_type, self.value_type: self.value}


@dataclass
class MultiSelectPageProperty(PageProperty):
    multi_select: list[SelectOption]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['multi_select']

    def _plain_serialize_type_object(self) -> Any:
        return self.multi_select


@dataclass
class NumberPageProperty(PageProperty):
    number: Union[int, Decimal]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['number']

    def _plain_serialize_type_object(self) -> Any:
        return self.number


@dataclass
class RelationPageProperty(PageProperty):
    page_ids: list[UUID]
    has_more: bool = field(init=False)

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['relation']

    def _plain_serialize_type_object(self) -> Any:
        return [{'id': page_id} for page_id in self.page_ids]

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars) -> Self:
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
    def _eligible_property_types(cls) -> list[str]:
        return ['rollup']

    def _plain_serialize_type_object(self) -> Any:
        return {'function': self.function, 'type': self.value_type, self.value_type: self.value}


@dataclass
class RichTextPageProperty(PageProperty):
    rich_text: list[RichText]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['rich_text', 'title']

    def _plain_serialize_type_object(self) -> Any:
        return self.rich_text


@dataclass
class SelectPageProperty(PageProperty):
    option: SelectOption

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['select', 'status']

    def _plain_serialize_type_object(self) -> Any:
        return self.option
