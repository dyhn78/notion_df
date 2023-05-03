from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal

from typing_extensions import Self

from notion_df.object.common import UUID
from notion_df.object.core import DualSerializable


@dataclass
class ParentResponse(DualSerializable):
    # https://developers.notion.com/reference/parent-object
    typename: Literal['database_id', 'page_id', 'block_id']
    id: UUID

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.typename,
            self.typename: self.id
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        parent_id = UUID(serialized[typename])
        return cls(typename, parent_id)

    def as_block(self, token: str):
        from notion_df.entity import Block, Database, Page
        match self.typename:
            case 'block_id':
                return Block(token, self.id)
            case 'database_id':
                return Database(token, self.id)
            case 'page_id':
                return Page(token, self.id)
