from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional, TYPE_CHECKING
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import DualSerializable

if TYPE_CHECKING:
    from notion_df.core.entity import Entity


@dataclass
class PartialParent(DualSerializable):
    # https://developers.notion.com/reference/parent-object
    typename: Literal['database_id', 'page_id', 'block_id', 'workspace']
    id: Optional[UUID]

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.typename,
            self.typename: str(self.id) if self.id else None
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        if typename == 'workspace':
            return cls('workspace', None)
        parent_id = UUID(serialized[typename])
        return cls(typename, parent_id)

    @property
    def entity(self) -> Optional[Entity]:
        from notion_df.entity import Block, Database, Page

        match self.typename:
            case 'block_id':
                return Block(self.id)
            case 'database_id':
                return Database(self.id)
            case 'page_id':
                return Page(self.id)
            case 'workspace':
                return None
