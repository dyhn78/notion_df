from __future__ import annotations

import inspect
from abc import ABCMeta
from collections.abc import MutableMapping
from dataclasses import dataclass, field
from typing import ClassVar, final, get_type_hints, get_origin, Literal, TypeVar, Generic, Any, Iterator, Optional
from uuid import UUID

from typing_extensions import Self

from notion_df.object.common import StatusGroups, SelectOptions
from notion_df.object.constant import NumberFormat, RollupFunction
from notion_df.object.filter import (
    PropertyFilter, FilterBuilder_T
)
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfAttributeError, NotionDfKeyError, NotionDfValueError
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
        if inspect.isabstract(cls):
            return
        for attr_name, attr_type in get_type_hints(cls).items():
            if get_origin(attr_type) == ClassVar and not hasattr(cls, attr_name):
                raise NotionDfAttributeError('all class attributes must be filled',
                                             {'cls': cls, 'attr_name': attr_name})

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
    def _deserialize_page_value(cls, prop_serialized: dict[str, Any], typename: str) -> PropertyValue_T:
        return deserialize(cls.page, prop_serialized[typename])


class Properties(DualSerializable, MutableMapping[PropertyKey, PropertyValue_T],
                 Generic[PropertyValue_T], metaclass=ABCMeta):
    key_by_id: dict[str, PropertyValue_T]
    key_by_name: dict[str, PropertyValue_T]

    def __init__(self, items: dict[PropertyKey, PropertyValue_T] = ()):
        self.items = items
        self.key_by_id = {}
        self.key_by_name = {}
        for key, value in items.items():
            self[key] = value

    def __repr__(self):
        return f'{type(self).__name__}({set(self.key_by_name.keys())})'

    def __iter__(self) -> Iterator[PropertyValue_T]:
        return iter(self.items)

    def __len__(self) -> int:
        return len(self.items)

    def _get_key(self, key: str | PropertyKey) -> PropertyKey:
        if isinstance(key, str):
            if key in self.key_by_id:
                return self.key_by_id[key]
            return self.key_by_name[key]
        if isinstance(key, PropertyKey):
            return key
        raise NotionDfKeyError('bad key', {'key': key})

    def __getitem__(self, key: str | PropertyKey) -> PropertyValue_T:
        return self.items[self._get_key(key)]

    def get(self, key: str | PropertyKey, default: Optional[PropertyValue_T] = None) -> Optional[PropertyValue_T]:
        key = self._get_key(key)
        try:
            return self[key]
        except KeyError:
            return default

    def __setitem__(self, key: str | PropertyKey, value: PropertyValue_T) -> None:
        self.key_by_id[key.id] = key
        self.key_by_name[key.name] = key
        self.items[key] = value

    def __delitem__(self, key: str | PropertyKey) -> None:
        key = self._get_key(key)
        self.key_by_name.pop(key.name)
        self.key_by_id.pop(key.id)
        self.items.pop(key)


class DatabaseProperties(Properties):
    def serialize(self) -> dict[str, Any]:
        return {key.name: {
            'type': key.typename,
            key.typename: serialize(value),
        } for key, value in self.items.items()}

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
        } for key, value in self.items.items()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls()
        for prop_name, prop_serialized in serialized.items():
            typename = prop_serialized['type']
            property_key_cls = property_key_registry[typename]
            property_key = property_key_cls(prop_name)
            property_key.id = prop_serialized['id']
            typename = prop_serialized['type']
            # noinspection PyProtectedMember
            property_value = property_key._deserialize_page_value(prop_serialized, typename)
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
    options: SelectOptions


@dataclass
class StatusDatabasePropertyValue(DatabasePropertyValue):
    """eligible property types: ['status']"""
    options: SelectOptions
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
        match (relation_type := serialized['relation']['type']):
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
