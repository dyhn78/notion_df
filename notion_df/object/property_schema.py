from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, cast

from typing_extensions import Self

from notion_df.object.core import Deserializable
from notion_df.object.misc import SelectOption, StatusGroups, RollupFunction, NumberFormat, UUID
from notion_df.util.collection import FinalClassDict
from notion_df.util.misc import NotionDfValueError


# TODO: configure Property -> DatabaseProperty 1:1 mapping, from Property's side.
#  access this mapping from Property (NOT DatabaseResponse), the base class.
#  Property.from_schema(schema: DatabaseProperty) -> Property
#  then, make Page or Database utilize it,
#  so that they could auto-configure itself and its children with the retrieved data.


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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != DatabaseProperty:
            self = super().deserialize(serialized)
        else:
            property_type = serialized['type']
            schema_type = database_property_by_property_type_dict[property_type]
            self = schema_type.deserialize(serialized)
        self = cast(Self, self)
        self.name = serialized['name']
        self.id = serialized['id']
        return self


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
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['number']

    format: NumberFormat

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {'format': self.format}


@dataclass
class SelectDatabaseProperty(DatabaseProperty):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['select', 'multi_select']

    options: list[SelectOption]

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {'options': self.options}


@dataclass
class StatusDatabaseProperty(DatabaseProperty):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['status']

    options: list[SelectOption]
    groups: list[StatusGroups]

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'options': self.options,
            'groups': self.groups
        }


@dataclass
class FormulaDatabaseProperty(DatabaseProperty):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['formula']

    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        pass  # TODO


@dataclass
class RelationDatabaseProperty(DatabaseProperty, metaclass=ABCMeta):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['relation']

    database_id: UUID

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
    database_id: UUID

    # TODO: double check

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationPropertySchema(RelationDatabaseProperty):
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    # TODO: double check

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
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['rollup']

    relation_property_name: str
    relation_property_id: str
    rollup_property_name: str
    rollup_property_id: str
    function: RollupFunction

    def _plain_serialize_type_object(self) -> dict[str, Any]:
        return {
            'relation_property_name': self.relation_property_name,
            'relation_property_id': self.relation_property_id,
            'rollup_property_name': self.rollup_property_name,
            'rollup_property_id': self.rollup_property_id,
            'function': self.function,
        }
