from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, ClassVar, overload

from typing_extensions import Self

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import SelectOption, StatusGroups, RollupFunction, NumberFormat, UUID


@dataclass
@set_master
class PropertySchema(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-schema-object
    # https://developers.notion.com/reference/update-property-schema-object
    type: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'type': self.type,
            self.type: self._plain_serialize_main()
        }

    @abstractmethod
    def _plain_serialize_main(self) -> dict[str, Any]:
        pass


@set_master
class Property(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/property-object
    schema: PropertySchema
    name: str
    id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            **self.schema
        }

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return Property(PropertySchema.deserialize(serialized), serialized['name'], serialized['id'])


@dataclass
class PlainPropertySchema(PropertySchema, metaclass=ABCMeta):
    """matching property types: 'title', 'rich_text', 'text', 'date', 'people', 'files', 'checkbox', 'url',
    'email', 'created_time', 'created_by', 'last_edited_time', 'last_edited_by'"""

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {}


class PropertyBuilder:
    # implement schema/property branching
    title = PlainPropertySchema('title')
    rich_text = PlainPropertySchema('rich_text')
    text = PlainPropertySchema('text')
    date = PlainPropertySchema('date')
    people = PlainPropertySchema('people')
    files = PlainPropertySchema('files')
    checkbox = PlainPropertySchema('files')
    url = PlainPropertySchema('url')
    email = PlainPropertySchema('email')
    created_time = PlainPropertySchema('created_time')
    created_by = PlainPropertySchema('created_by')
    last_edited_time = PlainPropertySchema('last_edited_time')
    last_edited_by = PlainPropertySchema('last_edited_by')


@dataclass
class NumberPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'number'

    format: NumberFormat

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class NumberProperty(Property, NumberPropertySchema):
    pass


@dataclass
class SelectPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'select'

    options: list[SelectOption]

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class SelectProperty(Property, SelectPropertySchema):
    pass


@dataclass
class StatusPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'status'

    options: list[SelectOption]
    groups: list[StatusGroups]

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }


@dataclass
class StatusProperty(Property, StatusPropertySchema):
    pass


@dataclass
class MultiSelectPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'multi_select'

    options: list[SelectOption]

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class MultiSelectProperty(Property, MultiSelectPropertySchema):
    pass


@dataclass
class FormulaPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'formula'

    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    def _plain_serialize_main(self) -> dict[str, Any]:
        pass  # TODO


@dataclass
class FormulaProperty(Property, FormulaPropertySchema):
    pass


@dataclass
class RelationPropertySchema(PropertySchema):
    database_id: UUID

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': self.type,
            self.type: self._plain_serialize_inner_value()
        }

    @abstractmethod
    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        pass


@dataclass
class RelationProperty(Property, RelationPropertySchema, metaclass=ABCMeta):
    pass


@dataclass
class SingleRelationPropertySchema(RelationPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'single_property'

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {}


@dataclass
class SingleRelationProperty(RelationProperty, SingleRelationPropertySchema):
    pass


@dataclass
class DualRelationPropertySchema(RelationPropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'dual_property'

    synced_property_name: str
    synced_property_id: str

    def _plain_serialize_inner_value(self) -> dict[str, Any]:
        return {
            'synced_property_name': self.synced_property_name,
            'synced_property_id': self.synced_property_id,
        }


@dataclass
class DualRelationProperty(RelationProperty, DualRelationPropertySchema):
    pass


@dataclass
class RollupPropertySchema(PropertySchema):
    @classmethod
    def _get_type(cls) -> str:
        return 'rollup'

    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str
    function: RollupFunction

    def _plain_serialize_main(self) -> dict[str, Any]:
        return {
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
            'function': self.function,
        }


@dataclass
class RollupProperty(Property, RollupPropertySchema):
    pass
