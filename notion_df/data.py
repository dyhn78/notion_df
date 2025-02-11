from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from functools import cache
from typing import Any, Optional, Union, get_type_hints
from uuid import UUID

from typing_extensions import Self

from notion_df.contents import (
    block_contents_registry,
    BlockContents,
    UnsupportedBlockContents,
)
from notion_df.core.data_core import EntityData
from notion_df.core.entity_core import Entity, RetrievableEntity
from notion_df.entity import Block, Database, Page, Workspace
from notion_df.file import File
from notion_df.misc import Icon, PartialParent
from notion_df.property import DatabaseProperties, PageProperties
from notion_df.rich_text import RichText
from notion_df.user import PartialUser


@cache
def _get_type_hints(cls) -> dict[str, type]:
    return get_type_hints(
        cls,
        {
            **globals(),
            **{
                cls.__name__: cls
                for cls in (
                    # TODO: UUID should be fetched from superclass definition instead
                    Entity,
                    RetrievableEntity,
                    Block,
                    Database,
                    Page,
                    Workspace,
                    UUID,
                )
            },
        },
    )


@dataclass
class BlockData(EntityData):
    parent: Union[Block, Page, Workspace]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    has_children: bool
    archived: bool
    contents: BlockContents

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]):
        typename = raw["type"]
        block_contents_cls = block_contents_registry.get(
            typename, UnsupportedBlockContents
        )
        block_contents = block_contents_cls.deserialize(raw[typename])
        return cls._deserialize_from_dict(
            raw,
            parent=PartialParent.deserialize(raw["parent"]).resolved,
            contents=block_contents,
        )

    @classmethod
    def _get_type_hints(cls) -> dict[str, type]:
        return _get_type_hints(cls)


@dataclass
class DatabaseData(EntityData):
    parent: Union[Block, Page, Workspace]
    created_time: datetime
    last_edited_time: datetime
    icon: Optional[Icon]
    cover: Optional[File]
    url: str
    title: RichText
    properties: DatabaseProperties
    archived: bool
    is_inline: bool

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(
            raw, parent=PartialParent.deserialize(raw["parent"]).resolved
        )

    @classmethod
    def _get_type_hints(cls) -> dict[str, type]:
        return _get_type_hints(cls)


@dataclass
class PageData(EntityData):
    parent: Union[Block, Database, Page, Workspace]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    icon: Optional[Icon]
    cover: Optional[File]
    url: str
    archived: bool
    properties: PageProperties

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(
            raw, parent=PartialParent.deserialize(raw["parent"]).resolved
        )

    @classmethod
    def _get_type_hints(cls) -> dict[str, type]:
        return _get_type_hints(cls)
