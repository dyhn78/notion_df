from __future__ import annotations

from abc import ABCMeta
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from datetime import datetime
from typing import ClassVar, final, TypeVar, Generic, Any, Iterator, Optional, Literal
from uuid import UUID

from typing_extensions import Self

from notion_df.object.common import StatusGroups, SelectOption, DateRange
from notion_df.object.constant import RollupFunction, NumberFormat, Number
from notion_df.object.file import Files
from notion_df.object.filter import PropertyFilter, FilterBuilder_T, CheckboxFilterBuilder, PeopleFilterBuilder, \
    DateFilterBuilder, TextFilterBuilder, FilesFilterBuilder, NumberFilterBuilder, MultiSelectFilterBuilder, \
    RelationFilterBuilder, SelectFilterBuilder
from notion_df.object.rich_text import RichText
from notion_df.object.user import PartialUser, User
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfKeyError, NotionDfValueError
from notion_df.util.misc import check_classvars_are_defined
from notion_df.util.serialization import DualSerializable, deserialize, serialize

PropertyValue_T = TypeVar('PropertyValue_T')
property_key_registry: FinalClassDict[str, type[PropertyKey]] = FinalClassDict()


class PropertyKey(Generic[FilterBuilder_T], metaclass=ABCMeta):
    typename: ClassVar[str]
    database: ClassVar[type]
    page: ClassVar[type]
    _filter_cls: type[FilterBuilder_T]

    def __init__(self, name: str):
        self.name = name
        self.id = None

    def __init_subclass__(cls, **kwargs):
        super().__init_subclass__(**kwargs)
        check_classvars_are_defined(cls)
        if typename := getattr(cls, 'typename', None):
            property_key_registry[typename] = cls

    @final
    @property
    def filter(self) -> FilterBuilder_T:
        def build(filter_condition: dict[str, Any]):
            return PropertyFilter(self.name, self._filter_cls.get_typename(), filter_condition)

        return self._filter_cls(build)

    # noinspection PyMethodMayBeStatic
    def _serialize_page_value(self, prop_value: PropertyValue_T) -> dict[str, Any]:
        return serialize(prop_value)

    @classmethod
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any]) -> PropertyValue_T:
        """allow proxy-deserialization of subclasses."""
        typename = prop_serialized['type']
        if cls == PropertyKey:
            subclass = property_key_registry[typename]
            return subclass._deserialize_page_value(prop_serialized)
        return deserialize(cls.page, prop_serialized[typename])


class Properties(DualSerializable, MutableMapping[PropertyKey[FilterBuilder_T], PropertyValue_T],
                 Generic[FilterBuilder_T, PropertyValue_T], metaclass=ABCMeta):
    key_by_id: dict[str, PropertyValue_T]
    key_by_name: dict[str, PropertyValue_T]

    def __init__(self, items: Optional[dict[PropertyKey, PropertyValue_T]] = None):
        self._items = {}
        self.key_by_id = {}
        self.key_by_name = {}
        if not items:
            return
        for key, value in items.items():
            self[key] = value

    def __repr__(self):
        return f'{type(self).__name__}({set(self.key_by_name.keys())})'

    def __iter__(self) -> Iterator[PropertyValue_T]:
        return iter(self._items)

    def __len__(self) -> int:
        return len(self._items)

    def _get_key(self, key: str | PropertyKey) -> PropertyKey:
        if isinstance(key, str):
            if key in self.key_by_id:
                return self.key_by_id[key]
            return self.key_by_name[key]
        if isinstance(key, PropertyKey):
            return key
        raise NotionDfKeyError('bad key', {'key': key})

    def __getitem__(self, key: str | PropertyKey) -> PropertyValue_T:
        return self._items[self._get_key(key)]

    def get(self, key: str | PropertyKey, default: Optional[PropertyValue_T] = None) -> Optional[PropertyValue_T]:
        key = self._get_key(key)
        try:
            return self[key]
        except KeyError:
            return default

    # TODO provide type hinting for each subclasses
    def __setitem__(self, key: str | PropertyKey, value: PropertyValue_T) -> None:
        self.key_by_id[key.id] = key
        self.key_by_name[key.name] = key
        self._items[key] = value

    def __delitem__(self, key: str | PropertyKey) -> None:
        key = self._get_key(key)
        self.key_by_name.pop(key.name)
        self.key_by_id.pop(key.id)
        self._items.pop(key)


class DatabaseProperties(Properties):
    def serialize(self) -> dict[str, Any]:
        return {key.name: {
            'type': key.typename,
            key.typename: serialize(value),
        } for key, value in self._items.items()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_key_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            property_value = deserialize(property_key.database, prop_serialized[typename])
            self[property_key] = property_value
        return self


class PageProperties(Properties):
    def serialize(self) -> dict[str, Any]:
        # noinspection PyProtectedMember
        return {key.name: {
            'type': key.typename,
            key.typename: key._serialize_page_value(value),
        } for key, value in self._items.items()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_key_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            # noinspection PyProtectedMember
            property_value = property_key_cls._deserialize_page_value(prop_serialized)
            self[property_key] = property_value
        return self


class DatabasePropertyValue(DualSerializable, metaclass=ABCMeta):
    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


@dataclass
class PlainDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ["title", "rich_text", "date", "people", "files", "checkbox", "url",
    "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]"""


@dataclass
class NumberDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['number']"""
    format: NumberFormat


@dataclass
class SelectDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['select', 'multi_select']"""
    options: list[SelectOption]


@dataclass
class StatusDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['status']"""
    options: list[SelectOption]
    groups: list[StatusGroups]


@dataclass
class FormulaDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['formula']"""
    expression: str = field()
    r"""example value: 'if(prop(\"In stock\"), 0, prop(\"Price\"))'"""


@dataclass
class RelationDatabasePropertyValue(DatabasePropertyValue, metaclass=ABCMeta):
    """eligible property types: ['relation']"""
    database_id: UUID

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationDatabasePropertyValue:
            return cls._deserialize_this(serialized)
        match (relation_type := serialized['type']):
            case 'single_property':
                subclass = SingleRelationDatabasePropertyValue
            case 'dual_property':
                subclass = DualRelationDatabasePropertyValue
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'relation_type': relation_type, 'serialized': serialized})
        return subclass.deserialize(serialized)


@dataclass
class SingleRelationDatabasePropertyValue(RelationDatabasePropertyValue):
    def serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationDatabasePropertyValue(RelationDatabasePropertyValue):
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
            database_id=serialized['database_id'],
            synced_property_name=serialized['dual_property']['synced_property_name'],
            synced_property_id=serialized['dual_property']['synced_property_id']
        )


@dataclass
class RollupDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['rollup']"""

    function: RollupFunction
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str


@dataclass
class RelationPagePropertyValue(DualSerializable):
    page_ids: list[UUID]
    has_more: bool = field(init=False, default=None)

    def serialize(self) -> Any:
        return [{'id': page_id} for page_id in self.page_ids]

    @classmethod
    def _deserialize_this(cls, serialized: list[dict[str, Any]]) -> Self:
        return cls(page_ids=[UUID(page['id']) for page in serialized])


@dataclass
class RollupPagePropertyValue(DualSerializable):
    # TODO: dynamically link rollup values to basic values (for example, RelationPageProperty, DatePageProperty)
    function: RollupFunction
    value_typename: Literal['array', 'date', 'number', 'incomplete', 'unsupported']
    value: Any

    def serialize(self) -> Any:
        return {'function': self.function,
                'type': self.value_typename,
                self.value_typename: self.value}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        value_typename = serialized['type']
        return cls(function=serialized['function'], value_typename=value_typename, value=serialized[value_typename])


class CheckboxPropertyKey(PropertyKey[CheckboxFilterBuilder]):
    typename = 'checkbox'
    database = PlainDatabasePropertyValue
    page = bool
    _filter_cls = CheckboxFilterBuilder


class CreatedByPropertyKey(PropertyKey[PeopleFilterBuilder]):
    typename = 'created_by'
    database = PlainDatabasePropertyValue
    page = PartialUser
    _filter_cls = PeopleFilterBuilder


class CreatedTimePropertyKey(PropertyKey[DateFilterBuilder]):
    typename = 'created_time'
    database = PlainDatabasePropertyValue
    page = datetime
    _filter_cls = DateFilterBuilder


class DatePropertyKey(PropertyKey[DateFilterBuilder]):
    typename = 'date'
    database = PlainDatabasePropertyValue
    page = DateRange
    _filter_cls = DateFilterBuilder


class EmailPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'email'
    database = PlainDatabasePropertyValue
    page = str
    _filter_cls = TextFilterBuilder


class FilesPropertyKey(PropertyKey[FilesFilterBuilder]):
    typename = 'files'
    database = PlainDatabasePropertyValue
    page = Files
    _filter_cls = FilesFilterBuilder


class FormulaPropertyKey(PropertyKey[FilterBuilder_T]):
    """cannot access page properties - use subclasses instead."""
    typename = 'formula'
    value_typename: ClassVar[str]
    page = None
    database = FormulaDatabasePropertyValue

    def _serialize_page_value(self, prop_value: PropertyValue_T) -> dict[str, Any]:
        return {'type': self.value_typename,
                self.value_typename: prop_value}


class BoolFormulaPropertyKey(FormulaPropertyKey[CheckboxFilterBuilder]):
    value_typename = 'boolean'
    page = bool
    _filter_cls = CheckboxFilterBuilder


class DateFormulaPropertyKey(FormulaPropertyKey[DateFilterBuilder]):
    value_typename = 'date'
    page = DateRange
    _filter_cls = DateFilterBuilder


class NumberFormulaPropertyKey(FormulaPropertyKey[NumberFilterBuilder]):
    value_typename = 'number'
    page = Number
    _filter_cls = NumberFilterBuilder


class StringFormulaPropertyKey(FormulaPropertyKey[TextFilterBuilder]):
    value_typename = 'string'
    page = str
    _filter_cls = TextFilterBuilder


class LastEditedByPropertyKey(PropertyKey[PeopleFilterBuilder]):
    typename = 'last_edited_by'
    database = PlainDatabasePropertyValue
    page = PartialUser
    _filter_cls = PeopleFilterBuilder


class LastEditedTimePropertyKey(PropertyKey[DateFilterBuilder]):
    typename = 'last_edited_time'
    database = PlainDatabasePropertyValue
    page = datetime
    _filter_cls = DateFilterBuilder


class MultiSelectPropertyKey(PropertyKey[MultiSelectFilterBuilder]):
    typename = 'multi_select'
    database = SelectDatabasePropertyValue
    page = list[SelectOption]
    _filter_cls = MultiSelectFilterBuilder


class NumberPropertyKey(PropertyKey[NumberFilterBuilder]):
    typename = 'number'
    database = NumberDatabasePropertyValue
    page = Number
    _filter_cls = NumberFilterBuilder


class PeoplePropertyKey(PropertyKey[PeopleFilterBuilder]):
    typename = 'people'
    database = PlainDatabasePropertyValue
    page = list[User]
    _filter_cls = PeopleFilterBuilder


class PhoneNumberPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'phone_number'
    database = PlainDatabasePropertyValue
    page = str
    _filter_cls = TextFilterBuilder


class RelationPropertyKey(PropertyKey[RelationFilterBuilder]):
    """cannot access database properties - use subclasses instead."""
    typename = 'relation'
    database = RelationDatabasePropertyValue
    page = RelationPagePropertyValue
    _filter_cls = RelationFilterBuilder

    @classmethod
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any]) -> PropertyValue_T:
        prop_value = super()._deserialize_page_value(prop_serialized)
        prop_value.has_more = prop_serialized['has_more']
        return prop_value


class SingleRelationPropertyKey(PropertyKey[RelationFilterBuilder]):
    database = SingleRelationDatabasePropertyValue


class DualRelationPropertyKey(PropertyKey[RelationFilterBuilder]):
    database = DualRelationDatabasePropertyValue


class RollupPropertyKey(PropertyKey):
    typename = 'rollup'
    database = RollupDatabasePropertyValue
    page = RollupPagePropertyValue  # TODO
    _filter_cls = None  # TODO


class RichTextPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'rich_text'
    database = PlainDatabasePropertyValue
    page = list[RichText]
    _filter_cls = TextFilterBuilder


class TitlePropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'title'
    database = PlainDatabasePropertyValue
    page = list[RichText]
    _filter_cls = TextFilterBuilder


class SelectPropertyKey(PropertyKey[SelectFilterBuilder]):
    typename = 'select'
    database = SelectDatabasePropertyValue
    page = SelectOption
    _filter_cls = SelectFilterBuilder


class StatusPropertyKey(PropertyKey[SelectFilterBuilder]):
    typename = 'status'
    database = StatusDatabasePropertyValue
    page = SelectOption
    _filter_cls = SelectFilterBuilder


class URLPropertyKey(PropertyKey[TextFilterBuilder]):
    typename = 'url'
    database = PlainDatabasePropertyValue
    page = str
    _filter_cls = TextFilterBuilder
