from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Any, TypeVar, Generic

from notion_df.resource.core import Deserializable
from notion_df.resource.misc import SelectOption, StatusGroups, RollupFunction, NumberFormat, UUID, RelationType

# TODO: configure Property -> PropertySchema 1:1 mapping, from Property's side.
#  access this mapping from Property (NOT DatabaseResponse), the base class.
#  Property.from_schema(schema: PropertySchema) -> Property
#  then, make Page or Database utilize it,
#  so that they could auto-configure itself and its children with the retrieved data.

PropertySchemaClause_T = TypeVar('PropertySchemaClause_T', bound=Deserializable)


@dataclass
class PartialPropertySchema(Deserializable, Generic[PropertySchemaClause_T], metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-schema-object
    # https://developers.notion.com/reference/update-property-schema-object
    clause: PropertySchemaClause_T
    type: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self.clause,
        }


@dataclass
class PropertySchema(PartialPropertySchema, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-object
    name: str
    id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return super()._plain_serialize() | {
            "name": self.name,
            "id": self.id,
        }


@dataclass
class PlainPropertySchemaClause(Deserializable):
    """available property types: ["title", "rich_text", "date", "people", "files", "checkbox", "url",
    "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]"""

    # noinspection PyMethodMayBeStatic
    def _plain_serialize(self) -> dict[str, Any]:
        return {}


@dataclass
class NumberPropertySchemaClause(Deserializable):
    """property types: ['number']"""
    format: NumberFormat

    def _plain_serialize(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class SelectPropertySchemaClause(Deserializable):
    """property types: ['select', 'multi_select']"""
    options: list[SelectOption]

    def _plain_serialize(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class StatusPropertySchemaClause(Deserializable):
    """property types: ['status']"""
    options: list[SelectOption]
    groups: list[StatusGroups]

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }


@dataclass
class FormulaPropertySchemaClause(Deserializable):
    """property types: ['formula']"""
    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    def _plain_serialize(self) -> dict[str, Any]:
        pass  # TODO


@dataclass
class _RelationPropertySchemaClause(Deserializable):
    """property types: ['relation']"""
    database_id: UUID
    relation_type: RelationType

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': self.relation_type,
            self.relation_type: {}
        }


@dataclass
class SingleRelationPropertySchemaClause(Deserializable):
    """property types: ['relation']"""
    database_id: UUID

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class SingleRelationPropertySchema:
    """property types: ['relation']"""
    database_id: UUID

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'single_property': {},
        }


@dataclass
class DualRelationPropertySchemaClause(Deserializable):
    """property types: ['relation']"""
    database_id: UUID

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'dual_property',
            'dual_property': {}
        }


@dataclass
class DualRelationPropertySchema:
    """property types: ['relation']"""
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "database_id": self.database_id,
            "synced_property_name": self.synced_property_name,
            "synced_property_id": self.synced_property_id,
        }


@dataclass
class RollupPropertySchemaClause(Deserializable):
    """property types: ['rollup']"""
    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str
    function: RollupFunction

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
            'function': self.function,
        }
