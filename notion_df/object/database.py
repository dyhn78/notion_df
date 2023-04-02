from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from typing_extensions import Self

from notion_df.object.core import Deserializable
from notion_df.object.file import ExternalFile
from notion_df.object.misc import UUID, Icon, NumberFormat, SelectOption, StatusGroups, RollupFunction
from notion_df.object.parent import Parent
from notion_df.object.rich_text import RichText
from notion_df.util.collection import FinalClassDict
from notion_df.util.misc import NotionDfValueError


@dataclass
class Database(Deserializable):
    # TODO: configure Property -> DatabaseProperty 1:1 mapping, from Property's side.
    #  access this mapping from Property (NOT DatabaseResponse), the base class.
    #  Property.from_schema(schema: DatabaseProperty) -> Property
    #  then, make Page or Database utilize it,
    #  so that they could auto-configure itself and its children with the retrieved data.
    id: UUID
    parent: Parent
    created_time: datetime
    last_edited_time: datetime
    icon: Icon
    cover: ExternalFile
    url: str
    title: list[RichText]
    properties: dict[str, DatabaseProperty] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    archived: bool
    is_inline: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": 'database',
            "id": self.id,
            "parent": self.parent,
            "created_time": self.created_time,
            "last_edited_time": self.last_edited_time,
            "icon": self.icon,
            "cover": self.cover,
            "url": self.url,
            "title": self.title,
            "properties": self.properties,
            "archived": self.archived,
            "is_inline": self.is_inline,
        }


@dataclass
class DatabaseProperty(Deserializable, metaclass=ABCMeta):
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

    @classmethod
    @abstractmethod
    def _eligible_property_types(cls) -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        for property_type in cls._eligible_property_types():
            database_property_by_property_type_dict[property_type] = cls

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self._plain_serialize_type_object(),
        }

    @abstractmethod
    def _plain_serialize_type_object(self) -> dict[str, Any]:
        pass

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_vars) -> Self:
        self = super()._plain_deserialize(serialized)
        self.name = serialized['name']
        self.id = serialized['id']
        return self

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != DatabaseProperty:
            return super().deserialize(serialized)
        else:
            property_type = serialized['type']
            schema_type = database_property_by_property_type_dict[property_type]
            return schema_type.deserialize(serialized)


database_property_by_property_type_dict = FinalClassDict[str, type[DatabaseProperty]]()


@dataclass
class PlainDatabaseProperty(DatabaseProperty):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ["title", "rich_text", "date", "people", "files", "checkbox", "url",
                "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]

    # noinspection PyMethodMayBeStatic
    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {}


@dataclass
class NumberDatabaseProperty(DatabaseProperty):
    format: NumberFormat

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['number']

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class SelectDatabaseProperty(DatabaseProperty):
    options: list[SelectOption]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['select', 'multi_select']

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class StatusDatabaseProperty(DatabaseProperty):
    options: list[SelectOption]

    groups: list[StatusGroups]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['status']

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }


@dataclass
class FormulaDatabaseProperty(DatabaseProperty):
    # TODO
    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['formula']

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        pass  # TODO


@dataclass
class RelationDatabaseProperty(DatabaseProperty, metaclass=ABCMeta):
    database_id: UUID

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['relation']

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationDatabaseProperty:
            return super().deserialize(serialized)
        match (relation_type := serialized['type']['type']):
            case 'single_property':
                subclass = SingleRelationPropertySchema
            case 'dual_property':
                subclass = DualRelationPropertySchema
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'relation_type': relation_type, 'serialized': serialized})
        return subclass.deserialize(serialized)


@dataclass
class SingleRelationPropertySchema(RelationDatabaseProperty):
    # TODO: double check
    database_id: UUID

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationPropertySchema(RelationDatabaseProperty):
    # TODO: double check
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'dual_property',
            'dual_property': {},
            "synced_property_name": self.synced_property_name,
            "synced_property_id": self.synced_property_id,
        }


@dataclass
class RollupDatabaseProperty(DatabaseProperty):
    # TODO: double check
    function: RollupFunction
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['rollup']

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'function': self.function,
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
        }
