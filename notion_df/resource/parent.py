from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Any

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import UUID


@set_master('type')
@dataclass
class Parent(Deserializable, metaclass=ABCMeta):
    # https://developers.notion.com/reference/parent-object
    id: UUID


@dataclass
class DatabaseParent(Parent):
    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": "database_id",
            "database_id": self.id
        }


@dataclass
class PageParent(Parent):
    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": "page_id",
            "page_id": self.id
        }


@dataclass
class BlockParent(Parent):
    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "type": "block_id",
            "block_id": self.id
        }
