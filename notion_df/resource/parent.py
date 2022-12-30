from __future__ import annotations

from abc import ABCMeta
from dataclasses import dataclass
from typing import Any

from notion_df.resource.core import Resource


@dataclass
class Parent(Resource, metaclass=ABCMeta):
    # https://developers.notion.com/reference/parent-object
    id: str


@dataclass
class DatabaseParent(Parent):
    def serialize_plain(self) -> dict[str, Any]:
        return {
            "type": "database_id",
            "database_id": self.id
        }


@dataclass
class PageParent(Parent):
    def serialize_plain(self) -> dict[str, Any]:
        return {
            "type": "page_id",
            "page_id": self.id
        }


@dataclass
class BlockParent(Parent):
    def serialize_plain(self) -> dict[str, Any]:
        return {
            "type": "block_id",
            "block_id": self.id
        }
