from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Any

from typing_extensions import Self

from notion_df.object.core import DualSerializable
from notion_df.object.misc import UUID


@dataclass
class Parent(DualSerializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/parent-object
    id: UUID

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        def get_subclass():
            match serialized['type']:
                case 'database_id':
                    return DatabaseParent
                case 'page_id':
                    return PageParent
                case 'block_id':
                    return BlockParent

        return get_subclass().deserialize(serialized)


@dataclass
class DatabaseParent(Parent):
    def serialize(self) -> dict[str, Any]:
        return {
            "type": "database_id",
            "database_id": self.id
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['database_id'])


@dataclass
class PageParent(Parent):
    def serialize(self) -> dict[str, Any]:
        return {
            "type": "page_id",
            "page_id": self.id
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['page_id'])


@dataclass
class BlockParent(Parent):
    def serialize(self) -> dict[str, Any]:
        return {
            "type": "block_id",
            "block_id": self.id
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['block_id'])
