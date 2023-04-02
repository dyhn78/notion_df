from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, cast

from typing_extensions import Self

from notion_df.resource.core import Deserializable
from notion_df.resource.misc import SelectOption, StatusGroups, RollupFunction, NumberFormat, UUID
from notion_df.util.collection import FinalClassDict
from notion_df.util.misc import NotionDfValueError


# TODO: configure Property -> PropertySchema 1:1 mapping, from Property's side.
#  access this mapping from Property (NOT DatabaseResponse), the base class.
#  Property.from_schema(schema: PropertySchema) -> Property
#  then, make Page or Database utilize it,
#  so that they could auto-configure itself and its children with the retrieved data.


@dataclass
class PropertySchema(Deserializable, metaclass=ABCMeta):
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
            schema_by_property_type_dict[property_type] = cls

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self._plain_serialize_contents(),
        }

    @abstractmethod
    def _plain_serialize_contents(self) -> dict[str, Any]:
        pass

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != PropertySchema:
            self = super().deserialize(serialized)
        else:
            property_type = serialized['type']
            schema_type = schema_by_property_type_dict[property_type]
            self = schema_type.deserialize(serialized)
        self = cast(Self, self)
        self.name = serialized['name']
        self.id = serialized['id']
        return self


schema_by_property_type_dict = FinalClassDict[str, type[PropertySchema]]()


@dataclass
class PlainPropertySchema(PropertySchema):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ["title", "rich_text", "date", "people", "files", "checkbox", "url",
                "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]

    # noinspection PyMethodMayBeStatic
    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {}


@dataclass
class NumberPropertySchema(PropertySchema):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['number']

    format: NumberFormat

    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class SelectPropertySchema(PropertySchema):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['select', 'multi_select']

    options: list[SelectOption]

    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class StatusPropertySchema(PropertySchema):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['status']

    options: list[SelectOption]
    groups: list[StatusGroups]

    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }


@dataclass
class FormulaPropertySchema(PropertySchema):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['formula']

    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    def _plain_serialize_contents(self) -> dict[str, Any]:
        pass  # TODO


@dataclass
class RelationPropertySchema(PropertySchema, metaclass=ABCMeta):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['relation']

    database_id: UUID

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationPropertySchema:
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
class SingleRelationPropertySchema(RelationPropertySchema):
    database_id: UUID

    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationPropertySchema(RelationPropertySchema):
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'dual_property',
            'dual_property': {},
            "synced_property_name": self.synced_property_name,
            "synced_property_id": self.synced_property_id,
        }


@dataclass
class RollupPropertySchema(PropertySchema):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['rollup']

    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str
    function: RollupFunction

    def _plain_serialize_contents(self) -> dict[str, Any]:
        return {
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
            'function': self.function,
        }
