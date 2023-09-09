from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from functools import cache
from typing import Any, Optional, Union, TYPE_CHECKING, get_type_hints, cast
from uuid import UUID

from typing_extensions import Self

from notion_df.core.request import Data
from notion_df.core.serialization import DualSerializable
from notion_df.data.common import Icon
from notion_df.data.constant import BlockColor, CodeLanguage
from notion_df.data.file import File
from notion_df.data.partial_parent import PartialParent
from notion_df.data.rich_text import Span, RichText
from notion_df.data.user import PartialUser
from notion_df.property import DatabaseProperties, PageProperties
from notion_df.util.collection import FinalDict

if TYPE_CHECKING:
    from notion_df.entity import Block, Database, Page


@dataclass
class DatabaseData(Data):
    id: UUID
    parent: Union[Block, Page, None]
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
        return cls._deserialize_from_dict(raw, raw=raw,
                                          parent=PartialParent.deserialize(raw['parent']).entity)

    @classmethod
    @cache
    def _get_type_hints(cls) -> dict[str, type]:
        # TODO deduplicate
        from notion_df.entity import Block, Database, Page
        from notion_df.core.entity_core import Entity
        return get_type_hints(cls, {**globals(), **{cls.__name__: cls for cls in (Entity, Block, Database, Page)}})


@dataclass
class PageData(Data):
    id: UUID
    parent: Union[Block, Database, Page, None]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    archived: bool
    icon: Optional[Icon]
    cover: Optional[File]
    url: str
    properties: PageProperties

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw, raw=raw,
                                          parent=PartialParent.deserialize(raw['parent']).entity)

    @classmethod
    @cache
    def _get_type_hints(cls) -> dict[str, type]:
        from notion_df.entity import Block, Database, Page
        from notion_df.core.entity_core import Entity
        return get_type_hints(cls, {**globals(), **{cls.__name__: cls for cls in (Entity, Block, Database, Page)}})


@dataclass
class BlockData(Data):
    id: UUID
    parent: Union[Block, Page, None]
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    has_children: Optional[bool]
    """Note: the None value never occurs from direct server data. It only happens from Page.as_block()"""
    archived: bool
    value: BlockValue

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]):
        typename = raw['type']
        block_value_cls = block_value_registry[typename]
        block_value = block_value_cls.deserialize(raw[typename])
        return cls._deserialize_from_dict(raw, raw=raw,
                                          parent=PartialParent.deserialize(raw['parent']).entity,
                                          value=block_value)

    @classmethod
    @cache
    def _get_type_hints(cls) -> dict[str, type]:
        from notion_df.entity import Block, Database, Page
        from notion_df.core.entity_core import Entity
        return get_type_hints(cls, {**globals(), **{cls.__name__: cls for cls in (Entity, Block, Database, Page)}})


block_value_registry: FinalDict[str, type[BlockValue]] = FinalDict()


@dataclass
class BlockValue(DualSerializable, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        return ''

    def __init_subclass__(cls, **kwargs):
        if (typename := cls.get_typename()) and typename != cast(cls, super(cls, cls)).get_typename():
            block_value_registry[typename] = cls

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


def serialize_block_value_list(block_value_list: Optional[list[BlockValue]]) -> Optional[list[dict[str, Any]]]:
    if block_value_list is None:
        return None
    return [{
        "object": "block",
        "type": block_type.get_typename(),
        block_type.get_typename(): block_type,
    } for block_type in block_value_list]


@dataclass
class BookmarkBlockValue(BlockValue):
    url: str
    caption: RichText = field(default_factory=RichText)

    @classmethod
    def get_typename(cls) -> str:
        return 'bookmark'


@dataclass
class BreadcrumbBlockValue(BlockValue):
    @classmethod
    def get_typename(cls) -> str:
        return 'breadcrumb'


@dataclass
class BulletedListItemBlockValue(BlockValue):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'bulleted_list_item'


@dataclass
class CalloutBlockValue(BlockValue):
    rich_text: RichText
    icon: Icon
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'callout'


@dataclass
class ChildDatabaseBlockValue(BlockValue):
    title: str

    @classmethod
    def get_typename(cls) -> str:
        return 'child_database'


@dataclass
class ChildPageBlockValue(BlockValue):
    title: str

    @classmethod
    def get_typename(cls) -> str:
        return 'child_page'


@dataclass
class CodeBlockValue(BlockValue):
    rich_text: RichText
    language: CodeLanguage = CodeLanguage.PLAIN_TEXT
    caption: RichText = field(default_factory=RichText)

    @classmethod
    def get_typename(cls) -> str:
        return 'code'


@dataclass
class ColumnListBlockValue(BlockValue):
    @classmethod
    def get_typename(cls) -> str:
        return 'column_list'


@dataclass
class ColumnBlockValue(BlockValue):
    @classmethod
    def get_typename(cls) -> str:
        return 'column'


@dataclass
class DividerBlockValue(BlockValue):
    @classmethod
    def get_typename(cls) -> str:
        return 'divider'


@dataclass
class EmbedBlockValue(BlockValue):
    url: str

    @classmethod
    def get_typename(cls) -> str:
        return 'embed'


@dataclass
class EquationBlockValue(BlockValue):
    expression: str
    """a KaTeX compatible string."""

    @classmethod
    def get_typename(cls) -> str:
        return 'equation'


@dataclass
class FileBlockValue(BlockValue):
    file: File
    caption: RichText = field(default_factory=RichText)

    @classmethod
    def get_typename(cls) -> str:
        return 'file'

    def serialize(self) -> dict[str, Any]:
        return {'caption': self.caption, **self.file.serialize()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized), serialized['caption'])


@dataclass
class Heading1BlockValue(BlockValue):
    rich_text: RichText
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_1'


@dataclass
class Heading2BlockValue(BlockValue):
    rich_text: RichText
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_2'


@dataclass
class Heading3BlockValue(BlockValue):
    rich_text: RichText
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_3'


@dataclass
class ImageBlockValue(BlockValue):
    """
    - The image must be directly hosted. In other words, the url cannot point to a service that retrieves the image.
    - supported image types (as of 2023-04-02): **.bmp .gif .heic .jpeg .jpg .png .svg .tif .tiff**
    https://developers.notion.com/reference/block#image
    """
    file: File

    def serialize(self) -> dict[str, Any]:
        return self.file.serialize()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized))

    @classmethod
    def get_typename(cls) -> str:
        return 'image'


@dataclass
class NumberedListItemBlockValue(BlockValue):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'numbered_list_item'


@dataclass
class ParagraphBlockValue(BlockValue):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'paragraph'


@dataclass
class PDFBlockValue(BlockValue):
    file: File
    caption: RichText = field(default_factory=RichText)

    def serialize(self) -> dict[str, Any]:
        return {'caption': self.caption, **self.file.serialize()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized), serialized['caption'])

    @classmethod
    def get_typename(cls) -> str:
        return 'pdf'


@dataclass
class QuoteBlockValue(BlockValue):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'quote'


@dataclass
class SyncedBlockValue(BlockValue, metaclass=ABCMeta):
    """cannot be changed (2023-04-02)"""

    @classmethod
    def get_typename(cls) -> str:
        return 'synced_block'

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        def get_subclass():
            if serialized['synced_from']:
                return DuplicatedSyncedBlockType
            else:
                return OriginalSyncedBlockType

        return get_subclass().deserialize(serialized)


@dataclass
class OriginalSyncedBlockType(SyncedBlockValue):
    """cannot be changed (2023-04-02)"""
    children: list[BlockData] = field(init=False, default=None)

    def serialize(self) -> dict[str, Any]:
        return {
            "synced_from": None,
            "children": self.children
        }


@dataclass
class DuplicatedSyncedBlockType(SyncedBlockValue):
    """cannot be changed (2023-04-02)"""
    block_id: UUID

    def serialize(self) -> dict[str, Any]:
        return {'synced_from': {'block_id': self.block_id}}


@dataclass
class TableBlockValue(BlockValue):
    table_width: int
    """cannot be changed."""
    has_column_header: bool
    has_row_header: bool

    @classmethod
    def get_typename(cls) -> str:
        return 'table'


@dataclass
class TableRowBlockValue(BlockValue):
    cells: list[list[Span]]
    """An array of cell contents in horizontal display order. Each cell is an array of rich text objects."""

    @classmethod
    def get_typename(cls) -> str:
        return 'table_row'


@dataclass
class TableOfContentsBlockValue(BlockValue):
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'table_of_contents'


@dataclass
class ToDoBlockValue(BlockValue):
    rich_text: RichText
    checked: bool
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'to_do'


@dataclass
class ToggleBlockValue(BlockValue):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'toggle'


@dataclass
class VideoBlockValue(BlockValue):
    """
    supported video types (as 2023-04-02):
    **.amv .asf .avi .f4v .flv .gifv .mkv .mov .mpg .mpeg .mpv .mp4 .m4v .qt .wmv**

    https://developers.notion.com/reference/block#supported-video-types
    """
    file: File

    def serialize(self) -> dict[str, Any]:
        return self.file.serialize()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized))

    @classmethod
    def get_typename(cls) -> str:
        return 'video'


@dataclass
class UnsupportedBlockValue(BlockValue):
    @classmethod
    def get_typename(cls) -> str:
        return 'unsupported'
