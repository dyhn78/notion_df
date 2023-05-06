from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from typing import TypeVar, Generic, Iterable, Any, Iterator, Optional, Final, final, Literal, Union
from uuid import UUID

from _decimal import Decimal
from typing_extensions import Self

from notion_df.object.common import DateRange, SelectOption, StatusGroups
from notion_df.object.constant import NumberFormat, RollupFunction
from notion_df.object.file import File
from notion_df.object.filter import (
    DateFilterType,
    FilterType_T
)
from notion_df.object.rich_text import RichText
from notion_df.object.user import PartialUser, User
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfKeyError, NotionDfValueError
from notion_df.util.misc import get_generic_arg
from notion_df.util.serialization import DualSerializable


@dataclass
class Property(DualSerializable, metaclass=ABCMeta):
    name: str
    id: str = field(init=False, default=None)


Property_T = TypeVar('Property_T', bound=Property)


class Properties(DualSerializable, Generic[Property_T]):
    by_id: dict[str, Property_T]
    by_name: dict[str, Property_T]
    _property_type: type[Property_T]

    def __init__(self, props: Iterable[Property_T] = ()):
        self.by_id = {}
        self.by_name = {}
        for prop in props:
            self.add(prop)

    def serialize(self) -> dict[str, Property_T]:
        return self.by_name

    def __init_subclass__(cls, **kwargs):
        if hasattr(cls, 'return_type'):
            return
        cls.return_type = get_generic_arg(cls, Property)

    def __repr__(self):
        return f'{type(self).__name__}({set(self.by_name.keys())})'

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, dict[str, Any]]) -> Self:
        properties = cls()
        for prop_name, prop_serialized in serialized.items():
            properties.add(cls._property_type.deserialize(prop_serialized))
        return properties

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


@dataclass
class DatabaseProperty(Property, metaclass=ABCMeta):
    """https://developers.notion.com/reference/property-object"""
    type: DatabasePropertyType

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        property_type_cls = property_type_registry[typename]
        database_property_type = property_type_cls.database.deserialize(serialized[typename])
        return cls._deserialize_from_dict(serialized, type=database_property_type)

    @final
    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.type.typename,
            self.type.typename: self.type
        }


class DatabasePropertyType(DualSerializable):
    typename: str

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


database_property_registry: FinalClassDict[str, type[DatabaseProperty]] = FinalClassDict()
database_property_type_registry: FinalClassDict[str, type[DatabasePropertyType]] = FinalClassDict()


class DatabaseProperties(Properties[DatabaseProperty]):
    pass


@dataclass
class PlainDatabasePropertyType(DatabasePropertyType):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ["title", "rich_text", "date", "people", "files", "checkbox", "url",
                "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]


@dataclass
class NumberDatabasePropertyType(DatabasePropertyType):
    format: NumberFormat

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['number']


@dataclass
class SelectDatabasePropertyType(DatabasePropertyType):
    options: list[SelectOption]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['select', 'multi_select']


@dataclass
class StatusDatabasePropertyType(DatabasePropertyType):
    options: list[SelectOption]
    groups: list[StatusGroups]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['status']


@dataclass
class FormulaDatabasePropertyType(DatabasePropertyType):
    # TODO
    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['formula']


@dataclass
class RelationDatabasePropertyType(DatabasePropertyType, metaclass=ABCMeta):
    database_id: UUID

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['relation']

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationDatabasePropertyType:
            return cls._deserialize_this(serialized)
        match (relation_type := serialized['type']):
            case 'single_property':
                subclass = SingleRelationPropertyType
            case 'dual_property':
                subclass = DualRelationPropertyType
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'relation_type': relation_type, 'serialized': serialized})
        return subclass.deserialize(serialized)


@dataclass
class SingleRelationPropertyType(RelationDatabasePropertyType):
    database_id: UUID

    def serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationPropertyType(RelationDatabasePropertyType):
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def serialize(self) -> dict[str, Any]:
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
            synced_property_name=serialized['dual_property']['synced_property_name'],
            synced_property_id=serialized['dual_property']['synced_property_id']
        )


@dataclass
class RollupDatabasePropertyType(DatabasePropertyType):
    # TODO: double check
    function: RollupFunction
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['rollup']


@dataclass
class PageProperty(Property, metaclass=ABCMeta):
    name: str = field(init=False, default=None)
    type: PagePropertyType


page_property_type_registry: FinalClassDict[str, type[PagePropertyType]] = FinalClassDict()


@dataclass
class PagePropertyType(DualSerializable, metaclass=ABCMeta):
    """https://developers.notion.com/reference/page-property-values"""

    @classmethod
    @cache
    def get_typename(cls) -> Optional[str]:
        """by default, return the first subclass-specific field's name.
        override this if the class definition does not comply the assumption."""
        # Note: this works only because python3.7+ dictates that dictionary is ordered as input order.
        for field_name in cls._get_type_hints():
            if field_name in PagePropertyType._get_type_hints():
                continue
            return field_name

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if typename := cls.get_typename():
            page_property_type_registry[typename] = cls

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls == PagePropertyType:
            subclass = page_property_type_registry[serialized['type']]
            return subclass.deserialize(serialized)
        return cls._deserialize_this(serialized)

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()


class PageProperties(Properties[PageProperty]):
    @classmethod
    def _deserialize_this(cls, serialized: dict[str, dict[str, Any]]) -> Self:
        properties = cls()
        for prop_name, prop_serialized in serialized.items():
            prop = cls._property_type.deserialize(prop_serialized)
            prop.name = prop_name
            properties.add(prop)
        return properties


@dataclass
class CheckboxPagePropertyType(PagePropertyType):
    checkbox: bool


@dataclass
class CreatedByPagePropertyType(PagePropertyType):
    created_by: PartialUser


@dataclass
class LastEditedByPagePropertyType(PagePropertyType):
    last_edited_by: PartialUser


@dataclass
class PeoplePagePropertyType(PagePropertyType):
    people: list[User]


@dataclass
class CreatedTimePagePropertyType(PagePropertyType):
    created_time: datetime


@dataclass
class LastEditedTimePagePropertyType(PagePropertyType):
    last_edited_time: datetime


@dataclass
class EmailPagePropertyType(PagePropertyType):
    email: str


@dataclass
class PhoneNumberPagePropertyType(PagePropertyType):
    phone_number: str


@dataclass
class URLPagePropertyType(PagePropertyType):
    url: str


@dataclass
class FilesPagePropertyType(PagePropertyType):
    files: list[File]


@dataclass
class FormulaPagePropertyType(PagePropertyType):
    value_type: Literal['boolean', 'date', 'number', 'string']
    value: Union[bool, datetime, int, Decimal, str]

    @classmethod
    def get_typename(cls) -> str:
        return 'formula'

    def serialize(self) -> Any:
        return {'type': 'formula',
                'formula': {'type': self.value_type, self.value_type: self.value}}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        property_type = serialized['formula']
        value_type = property_type['type']
        return cls._deserialize_from_dict(serialized, value_type=value_type, value=property_type[value_type])


@dataclass
class MultiSelectPagePropertyType(PagePropertyType):
    multi_select: list[SelectOption]


@dataclass
class NumberPagePropertyType(PagePropertyType):
    number: Union[int, Decimal]


@dataclass
class RelationPagePropertyType(PagePropertyType):
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
class RollupPagePropertyType(PagePropertyType):
    # TODO: dynamically link rollup values to basic values (for example, RelationPagePropertyType, DatePagePropertyType)
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
        property_type = serialized['rollup']
        value_type = property_type['type']
        return cls._deserialize_from_dict(serialized, function=property_type['function'],
                                          value_type=value_type, value=property_type[value_type])


@dataclass
class RichTextPagePropertyType(PagePropertyType):
    rich_text: list[RichText]


@dataclass
class TitlePagePropertyType(PagePropertyType):
    title: list[RichText]


@dataclass
class SelectPagePropertyType(PagePropertyType):
    select: SelectOption


@dataclass
class StatusPagePropertyType(PagePropertyType):
    status: SelectOption


DatabasePropertyType_T = TypeVar('DatabasePropertyType_T', bound=DatabasePropertyType)
PagePropertyType_T = TypeVar('PagePropertyType_T', bound=PagePropertyType)
property_type_registry: FinalClassDict[str, PropertyType] = FinalClassDict()


class PropertyType(Generic[DatabasePropertyType_T, PagePropertyType_T, FilterType_T]):
    def __new__(cls, typename: str,
                database: type[DatabasePropertyType_T],
                page: type[PagePropertyType_T],
                filter_type: type[FilterType_T]):
        if typename in property_type_registry:
            return property_type_registry[typename]
        self = super().__new__(cls)
        property_type_registry[typename] = self
        return self

    def __init__(self, typename: str,
                 database: type[DatabasePropertyType_T],
                 page: type[PagePropertyType_T],
                 filter_type: type[FilterType_T]):
        self.typename = typename
        self.database: Final[type[DatabasePropertyType_T]] = database
        self.page: type[PagePropertyType_T] = page
        self.filter_type: Final[type[FilterType_T]] = filter_type


@dataclass
class DatePagePropertyType(PagePropertyType):
    date: DateRange


date_property_type: PropertyType[PlainDatabasePropertyType, DatePagePropertyType, DateFilterType] = \
    PropertyType('date', PlainDatabasePropertyType, DatePagePropertyType, DateFilterType)


class DatePropertyType:
    database = PlainDatabasePropertyType
    page = DatePagePropertyType
    filter_type = DateFilterType

# @dataclass
# class PropertyType(metaclass=ABCMeta):
#     @classmethod
#     @abstractmethod
#     def get_typename(cls) -> str:
#         pass
#
#     def __init_subclass__(cls, **kwargs) -> None:
#         super().__init_subclass__(**kwargs)
#         if inspect.isabstract(cls):
#             return
#         property_type_registry[cls.get_typename()] = cls
#
#     @property
#     @abstractmethod
#     def filter(self) -> FilterType[FilterTypeDepr]:
#         pass
#
#     def _filter_builder(self, filter_type: dict) -> FilterTypeDepr:
#         """helper class to define filter()."""
#         return FilterTypeDepr(filter_type, self.get_typename())


# @dataclass
# class TitlePropertyType(PropertyType):
#     @classmethod
#     def get_typename(cls) -> str:
#         return 'title'
#
#     @property
#     def filter(self) -> TextFilterType[FilterTypeDepr]:
#         return TextFilterType(self._filter_builder)
#
#
# @dataclass
# class RichTextPropertyType(PropertyType):
#     @classmethod
#     def get_typename(cls) -> str:
#         return 'rich_text'
#
#     @property
#     def filter(self) -> TextFilterType[FilterTypeDepr]:
#         return TextFilterType(self._filter_builder)
#
#
# @dataclass
# class DatePropertyType(PropertyType):
#     @classmethod
#     def get_typename(cls) -> str:
#         return 'date'
#
#     @property
#     def filter(self) -> DateFilterType[FilterTypeDepr]:
#         return DateFilterType(self._filter_builder)
#
#
# @dataclass
# class PeoplePropertyType(PropertyType):
#     @classmethod
#     def get_typename(cls) -> str:
#         return 'people'
#
#     @property
#     def filter(self) -> PeopleFilterType[FilterTypeDepr]:
#         return PeopleFilterType(self._filter_builder)
