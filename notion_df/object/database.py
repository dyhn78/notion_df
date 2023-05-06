from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field, fields
from datetime import datetime
from functools import cache
from typing import Any, Optional, final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.request import Response
from notion_df.object.common import SelectOption, StatusGroups, Icon, Properties, Property
from notion_df.object.constant import NumberFormat, RollupFunction
from notion_df.object.file import ExternalFile
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.util.collection import FinalClassDict
from notion_df.util.exception import NotionDfValueError

database_property_registry: FinalClassDict[str, type[DatabaseProperty]] = FinalClassDict()


@dataclass
class DatabaseResponse(Response):
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
class DatabaseProperty(Property, metaclass=ABCMeta):
    """https://developers.notion.com/reference/property-object"""
    type: str
    name: str = field(init=True)

    @classmethod
    @abstractmethod
    def _eligible_property_types(cls) -> list[str]:
        pass

    @classmethod
    @cache
    def _get_type_specific_fields(cls) -> set[str]:
        return {fd.name for fd in fields(cls) if fd.name not in DatabaseProperty._get_type_hints()}

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        if cls._eligible_property_types():
            for property_type in cls._eligible_property_types():
                database_property_registry[property_type] = cls

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls == DatabaseProperty:
            typename = serialized['type']
            subclass = database_property_registry[typename]
            return subclass.deserialize(serialized)
        return cls._deserialize_this(serialized)

    @final
    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self._serialize_type_object()
        }

    def _serialize_type_object(self) -> dict[str, Any]:
        return {fd_name: fd_value for fd_name, fd_value in self._serialize_as_dict().items()
                if fd_name in self._get_type_specific_fields()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        type_object = serialized[serialized['type']]
        return cls._deserialize_from_dict(serialized, **{
            fd_name: type_object[fd_name] for fd_name in cls._get_type_specific_fields()})


class DatabaseProperties(Properties[DatabaseProperty]):
    pass


@dataclass
class PlainDatabaseProperty(DatabaseProperty):
    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ["title", "rich_text", "date", "people", "files", "checkbox", "url",
                "email", "phone_number", "created_time", "created_by", "last_edited_time", "last_edited_by"]


@dataclass
class NumberDatabaseProperty(DatabaseProperty):
    format: NumberFormat

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['number']


@dataclass
class SelectDatabaseProperty(DatabaseProperty):
    options: list[SelectOption]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['select', 'multi_select']


@dataclass
class StatusDatabaseProperty(DatabaseProperty):
    options: list[SelectOption]
    groups: list[StatusGroups]

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['status']


@dataclass
class FormulaDatabaseProperty(DatabaseProperty):
    # TODO
    expression: str = field()
    r'''example value: "if(prop(\"In stock\"), 0, prop(\"Price\"))"'''

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['formula']


@dataclass
class RelationDatabaseProperty(DatabaseProperty, metaclass=ABCMeta):
    database_id: UUID

    @classmethod
    def _eligible_property_types(cls) -> list[str]:
        return ['relation']

    # @classmethod
    # def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
    #     return cls._deserialize_from_dict(serialized)

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != RelationDatabaseProperty:
            return cls._deserialize_this(serialized)
        match (relation_type := serialized['relation']['type']):
            case 'single_property':
                subclass = SingleRelationProperty
            case 'dual_property':
                subclass = DualRelationProperty
            case _:
                raise NotionDfValueError('invalid relation_type',
                                         {'relation_type': relation_type, 'serialized': serialized})
        return subclass.deserialize(serialized)


@dataclass
class SingleRelationProperty(RelationDatabaseProperty):
    database_id: UUID

    def _serialize_type_object(self) -> dict[str, Any]:
        return super().serialize() | {
            'database_id': self.database_id,
            'type': 'single_property',
            'single_property': {}
        }


@dataclass
class DualRelationProperty(RelationDatabaseProperty):
    database_id: UUID
    synced_property_name: str
    synced_property_id: str

    def _serialize_type_object(self) -> dict[str, Any]:
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
            database_id=serialized['relation']['database_id'],
            synced_property_name=serialized['relation']['dual_property']['synced_property_name'],
            synced_property_id=serialized['relation']['dual_property']['synced_property_id']
        )


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
