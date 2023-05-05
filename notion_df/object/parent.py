from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal, Optional
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import DualSerializable


@dataclass
class ParentInfo(DualSerializable):
    # https://developers.notion.com/reference/parent-object
    typename: Literal['database_id', 'page_id', 'block_id', 'workspace']
    id: Optional[UUID]

    def serialize(self) -> dict[str, Any]:
        return {
            "type": self.typename,
            self.typename: self.id
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        if typename == 'workspace':
            return cls('workspace', None)
        parent_id = UUID(serialized[typename])
        return cls(typename, parent_id)
