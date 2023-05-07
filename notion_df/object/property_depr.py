from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field, fields
from datetime import datetime
from functools import cache
from typing import TypeVar, Generic, Iterable, Any, Iterator, Optional, final, Literal, Union
from uuid import UUID

from _decimal import Decimal
from typing_extensions import Self

from notion_df.object.common import DateRange, SelectOption, StatusGroups
from notion_df.object.constant import NumberFormat, RollupFunction
from notion_df.object.file import File
from notion_df.object.filter import (
    DateFilterBuilder,
    PropertyFilter, FilterBuilder
)
from notion_df.object.rich_text import RichText
from notion_df.object.user import PartialUser, User
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfKeyError, NotionDfValueError
from notion_df.util.serialization import DualSerializable

Property_T = TypeVar('Property_T', bound='Property')
PropertyType_T = TypeVar('PropertyType_T', bound='PropertyType')
DatabaseProperty_T = TypeVar('DatabaseProperty_T', bound='DatabaseProperty')
PageProperty_T = TypeVar('PageProperty_T', bound='PageProperty')
property_type_registry: FinalClassDict[str, PropertyType] = FinalClassDict()


@dataclass
class Property(DualSerializable, metaclass=ABCMeta):
    name: str
    id: str = field(init=False, default=None)
    type: PropertyType = field(init=False)


@dataclass
class PageProperty(Property, metaclass=ABCMeta):
    """https://developers.notion.com/reference/page-property-values"""

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls == DatabaseProperty:
            typename = serialized['type']
            property_type = property_type_registry[typename]
            serialized['type'] = property_type
            return property_type.page.deserialize(serialized)
        return cls._deserialize_this(serialized)

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


@dataclass
class DatabaseProperty(Property, metaclass=ABCMeta):
    """https://developers.notion.com/reference/property-object"""

    @classmethod
    @cache
    def _get_type_specific_fields(cls) -> set[str]:
        return {fd.name for fd in fields(cls) if fd.name not in DatabaseProperty._get_type_hints()}

    def _serialize_type_object(self) -> dict[str, Any]:
        return {fd_name: fd_value for fd_name, fd_value in self._serialize_as_dict().items()
                if fd_name in self._get_type_specific_fields()}

    @final
    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.type.name,
            self.type.name: self._serialize_type_object()
        }

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls == DatabaseProperty:
            typename = serialized['type']
            property_type = property_type_registry[typename]
            serialized['type'] = property_type
            return property_type.database.deserialize(serialized)
        return cls._deserialize_this(serialized)

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        type_object = serialized[serialized['type']]
        return cls._deserialize_from_dict(serialized, **{
            fd_name: type_object[fd_name] for fd_name in cls._get_type_specific_fields()})


@dataclass
class PlainDatabaseProperty(DatabaseProperty):
    """eligible property types: ["title", "rich_text", "date", "people", "files", "checkbox", "url",
    "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]"""


@dataclass
class NumberDatabaseProperty(DatabaseProperty):
    """eligible property types: ['number']"""
    format: NumberFormat


@dataclass
class SelectDatabaseProperty(DatabaseProperty):
    """eligible property types: ['select', 'multi_select']"""
    options: list[SelectOption]


@dataclass
class StatusDatabaseProperty(DatabaseProperty):
    """eligible property types: ['status']"""
    options: list[SelectOption]
    groups: list[StatusGroups]


@dataclass
class FormulaDatabaseProperty(DatabaseProperty):
    """eligible property types: ['formula']"""
    # TODO
    expression: str = field()
    r"""example value: 'if(prop(\"In stock\"), 0, prop(\"Price\"))'"""


@dataclass
class RelationDatabaseProperty(DatabaseProperty, metaclass=ABCMeta):
    """eligible property types: ['relation']"""
    database_id: UUID

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationDatabaseProperty:
            return cls._deserialize_this(serialized)
        match (relation_type := serialized['relation']['type']):
            case 'single_property':
                subclass = SingleRelationProperty
            case 'dual_property':
                subclass = DualRelationProperty
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'relation_type': relation_type, 'serialized': serialized})
        return subclass.deserialize(serialized)


@dataclass
class SingleRelationProperty(RelationDatabaseProperty):
    database_id: UUID

    def _serialize_type_object(self) -> dict[str, Any]:
        return super().serialize() | {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationProperty(RelationDatabaseProperty):
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def _serialize_type_object(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'dual_property',
            'dual_property': {'synced_property_name': self.synced_property_name,
                              'synced_property_id': self.synced_property_id}
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(
            serialized,
            database_id=serialized['relation']['database_id'],
            synced_property_name=serialized['relation']['dual_property']['synced_property_name'],
            synced_property_id=serialized['relation']['dual_property']['synced_property_id']
        )


@dataclass
class RollupDatabaseProperty(DatabaseProperty):
    """eligible property types: ['rollup']"""

    function: RollupFunction
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str


@dataclass
class CheckboxPageProperty(PageProperty):
    checkbox: bool


@dataclass
class CreatedByPageProperty(PageProperty):
    created_by: PartialUser


@dataclass
class CreatedTimePageProperty(PageProperty):
    created_time: datetime


@dataclass
class DatePageProperty(PageProperty):
    date: DateRange


@dataclass
class EmailPageProperty(PageProperty):
    email: str


@dataclass
class LastEditedByPageProperty(PageProperty):
    last_edited_by: PartialUser


@dataclass
class LastEditedTimePageProperty(PageProperty):
    last_edited_time: datetime


@dataclass
class PeoplePageProperty(PageProperty):
    people: list[User]


@dataclass
class PhoneNumberPageProperty(PageProperty):
    phone_number: str


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
        return {'type': 'formula',
                'formula': {'type': self.value_type,
                            self.value_type: self.value}}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        value_object = serialized['formula']
        value_type = value_object['type']
        return cls._deserialize_from_dict(serialized, value_type=value_type, value=value_object[value_type])


@dataclass
class MultiSelectPageProperty(PageProperty):
    multi_select: list[SelectOption]


@dataclass
class NumberPageProperty(PageProperty):
    number: Union[int, Decimal]


@dataclass
class RelationPageProperty(PageProperty):
    page_ids: list[UUID]
    has_more: bool = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'relation'

    def serialize(self) -> Any:
        return {'type': 'relation',
                'relation': [{'id': page_id} for page_id in self.page_ids]}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized, page_ids=[UUID(page['id']) for page in serialized['relation']])


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
        return {'type': 'rollup',
                'rollup': {'function': self.function,
                           'type': self.value_type,
                           self.value_type: self.value}}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        value_object = serialized['rollup']
        value_type = value_object['type']
        return cls._deserialize_from_dict(serialized, function=value_object['function'],
                                          value_type=value_type, value=value_object[value_type])


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


@dataclass
class URLPageProperty(PageProperty):
    url: str


@dataclass
class PropertyType(metaclass=ABCMeta):
    _filter_cls: type[FilterBuilder]

    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if inspect.isabstract(cls):
            return
        property_type_registry[cls.get_typename()] = cls

    @classmethod
    def filter(cls, name_or_id: str) -> FilterBuilder:
        return cls._filter_cls(lambda filter_condition: PropertyFilter(
            name_or_id, cls._filter_cls.get_typename(), filter_condition))

    @property
    @abstractmethod
    def filter(self) -> FilterBuilder[FilterTypeDepr]:
        pass

    def _build_filter(self, filter_condition: dict) -> PropertyFilter:
        """helper class to define filter()."""
        return PropertyFilter(self.name, self.get_typename(), filter_condition)


@dataclass
class TitlePropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'title'

    @property
    def filter(self) -> TextFilterBuilder:
        return TextFilterBuilder(self._filter_builder)


@dataclass
class RichTextPropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'rich_text'

    @property
    def filter(self) -> TextFilterBuilder:
        return TextFilterBuilder(self._filter_builder)


@dataclass
class DatePropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'date'

    @property
    def filter(self) -> DateFilterBuilder:
        return DateFilterBuilder(self._filter_builder)


@dataclass
class PeoplePropertyType(PropertyType):
    @classmethod
    def get_typename(cls) -> str:
        return 'people'

    @property
    def filter(self) -> PeopleFilterBuilder:
        return PeopleFilterBuilder(self._filter_builder)


class Properties(DualSerializable, Generic[Property_T], metaclass=ABCMeta):
    by_id: dict[str, Property_T]
    by_name: dict[str, Property_T]

    def __init__(self, props: Iterable[Property_T] = ()):
        self.by_id = {}
        self.by_name = {}
        for prop in props:
            self.add(prop)

    def serialize(self) -> dict[str, Property_T]:
        return self.by_name

    def __repr__(self):
        return f'{type(self).__name__}({set(self.by_name.keys())})'

    def __iter__(self) -> Iterator[Property_T]:
        return iter(self.by_id.values())

    def __getitem__(self, key: str | Property_T) -> Property_T:
        if isinstance(key, str):
            if key in self.by_id:
                return self.by_id[key]
            return self.by_name[key]
        if isinstance(key, Property):
            return self.by_name[key.name]
        raise NotionDfKeyError('bad key', {'key': key})

    def __delitem__(self, key: str | Property_T) -> None:
        self.pop(self[key])

    def get(self, key: str | Property_T) -> Optional[Property_T]:
        try:
            return self[key]
        except KeyError:
            return None

    def add(self, prop: Property_T) -> None:
        self.by_id[prop.id] = prop
        self.by_name[prop.name] = prop

    def pop(self, prop: Property_T) -> Property_T:
        self.by_name.pop(prop.name)
        return self.by_id.pop(prop.id)


class DatabaseProperties(Properties[DatabaseProperty]):
    @classmethod
    def _deserialize_this(cls, serialized: dict[str, dict[str, Any]]) -> Self:
        properties = cls()
        for prop_name, prop_serialized in serialized.items():
            properties.add(DatabaseProperty.deserialize(prop_serialized))
        return properties


class PageProperties(Properties[PageProperty]):
    @classmethod
    def _deserialize_this(cls, serialized: dict[str, dict[str, Any]]) -> Self:
        properties = cls()
        for prop_name, prop_serialized in serialized.items():
            prop_serialized['name'] = prop_name
            properties.add(PageProperty.deserialize(prop_serialized))
        return properties
