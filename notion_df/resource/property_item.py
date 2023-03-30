from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any

from typing_extensions import Self

from notion_df.resource.core import Deserializable
from notion_df.util.collection import FinalDict


@dataclass
class PartialPropertyItem(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    clause: PropertyItemClause
    type: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self.clause,
        }

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != PartialPropertyItem:
            return super().deserialize(serialized)
        property_type = serialized['type']
        item_clause_type = item_clause_by_property_type_dict[property_type]
        clause = item_clause_type.deserialize(serialized)
        return cls(clause, property_type)


@dataclass
class PropertyItem(PartialPropertyItem, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    name: str
    id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return super()._plain_serialize() | {
            "name": self.name,
            "id": self.id,
        }

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        if cls != PropertyItem:
            return super().deserialize(serialized)
        partial = super().deserialize(serialized)
        return cls(partial.clause, partial.type, serialized['name'], serialized['id'])


item_clause_by_property_type_dict: FinalDict[str, type[PropertyItemClause]] = FinalDict()


@dataclass
class PropertyItemClause(Deserializable, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def _eligible_property_types(cls) -> list[str]:
        pass

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        for property_type in cls._eligible_property_types():
            item_clause_by_property_type_dict[property_type] = cls
