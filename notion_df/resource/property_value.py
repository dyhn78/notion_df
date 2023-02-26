from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass
from typing import Any, ClassVar, TypeVar

from notion_df.resource.core import Deserializable

PropertyValueClause_T = TypeVar('PropertyValueClause_T')


@dataclass
class PropertyValue(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/page-property-values
    type: ClassVar[str]
    clause: PropertyValueClause_T
    name: str
    id: str

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "type": self.type,
            self.type: self.clause,
        }

    @abstractmethod
    def _plain_serialize_inner_value(self):
        pass
