from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from typing_extensions import Self

from notion_df.core.request import Response
from notion_df.core.serialization import DualSerializable
from notion_df.object.common import SelectOption, StatusGroups, Icon, Properties, Property
from notion_df.object.constant import NumberFormat, RollupFunction
from notion_df.object.file import ExternalFile
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfValueError

database_property_type_registry: FinalClassDict[str, type[DatabasePropertyType]] = FinalClassDict()


@dataclass
class DatabaseResponse(Response):
    # TODO: configure Property -> DatabaseProperty 1:1 mapping, from Property's side.
    #  access this mapping from Property (NOT DatabaseResponse), the base class.
    #  Property.from_schema(schema: DatabaseProperty) -> Property
    #  then, make Page or Database utilize it,
    #  so that they could autoconfigure itself and its children with the retrieved data.
    id: UUID
    parent: ParentInfo
    created_time: datetime
    last_edited_time: datetime
    icon: Optional[Icon]
    cover: Optional[ExternalFile]
    url: str
    title: list[RichText]
    properties: DatabaseProperties
    archived: bool
    is_inline: bool

    @classmethod
    def _deserialize_this(cls, response_data: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(response_data)


@dataclass
class DatabaseProperty(Property):
    """
    represents two types of data structure.

    - partial property schema - user side
    - property schema - server side

    property schema has additional fields, `name` and `id`. these are hidden from __init__() to prevent confusion.

    - https://developers.notion.com/reference/property-schema-object
    - https://developers.notion.com/reference/update-property-schema-object
    """
    type: str
    property_type: DatabasePropertyType

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self.property_type.serialize()
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        property_type_cls = database_property_type_registry[typename]
        property_type = property_type_cls.deserialize(serialized[typename])
        return cls._deserialize_from_dict(serialized, property_type=property_type)


class DatabaseProperties(Properties[DatabaseProperty]):
    pass


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
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


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

    # @classmethod
    # def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
    #     return cls._deserialize_from_dict(serialized)

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

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['database_id'],
                   serialized['dual_property']['synced_property_name'],
                   serialized['dual_property']['synced_property_id'])


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
