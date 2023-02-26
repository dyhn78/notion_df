from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar

from notion_df.resource.core import Deserializable

PropertyValueClause_T = TypeVar('PropertyValueClause_T')


@dataclass
class PartialPropertyItem(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    clause: PropertyValueClause_T
    type: ClassVar[str]

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": self.type,
            self.type: self.clause,
        }


@dataclass
class PropertyItem(PartialPropertyItem, metaclass=ABCMeta):
    name: str
    id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return super()._plain_serialize() | {
            "name": self.name,
            "id": self.id,
        }
