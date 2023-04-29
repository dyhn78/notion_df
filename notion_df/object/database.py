from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from typing_extensions import Self

from notion_df.object.core import DualSerializable
from notion_df.object.misc import UUID, NumberFormat, SelectOption, StatusGroups, RollupFunction
from notion_df.util.collection import FinalClassDict
from notion_df.util.misc import NotionDfValueError


@dataclass
class DatabaseProperty(DualSerializable, metaclass=ABCMeta):
    """
    represents two types of data structure.

    - partial property schema - user side
    - property schema - server side

    property schema has additional fields, `name` and `id`. these are hidden from __init__() to prevent confusion.

    - https://developers.notion.com/reference/property-schema-object
    - https://developers.notion.com/reference/update-property-schema-object
    """
    type: str
    name: str = field(init=False)
    id: str = field(init=False)
    type_object: DatabasePropertyType

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self.type_object.serialize()
        }

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        type_object_cls = database_property_type_registry[typename]
        type_object = type_object_cls.deserialize(serialized[typename])
        return cls._deserialize_asdict(serialized | {'type_object': type_object})


database_property_type_registry: FinalClassDict[str, type[DatabasePropertyType]] = FinalClassDict()


class DatabasePropertyType(DualSerializable, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def _eligible_property_types(cls) -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        for property_type in cls._eligible_property_types():
            database_property_type_registry[property_type] = cls

    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(serialized)


@dataclass
class PlainDatabaseProperty(DatabasePropertyType):
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
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(serialized)

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
        return subclass._deserialize_this(serialized)


@dataclass
class SingleRelationPropertyType(RelationDatabasePropertyType):
    # TODO: double check
    database_id: UUID

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationPropertyType(RelationDatabasePropertyType):
    # TODO: double check
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def serialize(self) -> dict[str, Any]:
        return super().serialize() | {
            'type': 'dual_property',
            'dual_property': {},
        }


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
