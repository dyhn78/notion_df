from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Optional

from typing_extensions import Self

from notion_df.core.response import Response
from notion_df.core.serialization import DualSerializable
from notion_df.object.common import UUID, Icon
from notion_df.object.constant import BlockColor, CodeLanguage
from notion_df.object.file import File
from notion_df.object.parent import ParentInfo
from notion_df.object.rich_text import RichText
from notion_df.object.user import User
from notion_df.util.collection import FinalClassDict

block_type_registry: FinalClassDict[str, type[BlockType]] = FinalClassDict()


@dataclass
class BlockResponse(Response):
    id: UUID
    parent: ParentInfo
    created_time: datetime
    last_edited_time: datetime
    created_by: User
    last_edited_by: User
    has_children: Optional[bool]
    """the None value never occurs from direct server response. It only happens from Page.as_block()"""
    archived: bool
    block_type: BlockType

    @classmethod
    def _deserialize_this(cls, response_data: dict[str, Any]):
        typename = response_data['type']
        block_type_cls = block_type_registry[typename]
        block_type = block_type_cls.deserialize(response_data[typename])
        return cls._deserialize_from_dict(response_data, block_type=block_type)


def serialize_partial_block_list(block_type_list: list[BlockType]) -> list[dict[str, Any]]:
    return [{
        "object": "block",
        "type": block_type.get_typename(),
        block_type.get_typename(): block_type,
    } for block_type in block_type_list]


@dataclass
class BlockType(DualSerializable, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass

    def __init_subclass__(cls, **kwargs):
        block_type_registry[cls.get_typename()] = cls

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(serialized)


@dataclass
class BookmarkBlockType(BlockType):
    url: str
    caption: list[RichText] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'bookmark'


@dataclass
class BreadcrumbBlockType(BlockType):
    @classmethod
    def get_typename(cls) -> str:
        return 'breadcrumb'


@dataclass
class BulletedListItemBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'bulleted_list_item'


@dataclass
class CalloutBlockType(BlockType):
    rich_text: list[RichText]
    icon: Icon
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)  # TODO: double check

    @classmethod
    def get_typename(cls) -> str:
        return 'callout'


@dataclass
class ChildDatabaseBlockType(BlockType):
    title: str

    @classmethod
    def get_typename(cls) -> str:
        return 'child_database'


@dataclass
class ChildPageBlockType(BlockType):
    title: str

    @classmethod
    def get_typename(cls) -> str:
        return 'child_page'


@dataclass
class CodeBlockType(BlockType):
    rich_text: list[RichText]
    language: CodeLanguage
    caption: list[RichText] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'code'


@dataclass
class ColumnListBlockType(BlockType):
    @classmethod
    def get_typename(cls) -> str:
        return 'column_list'


@dataclass
class ColumnBlockType(BlockType):
    @classmethod
    def get_typename(cls) -> str:
        return 'column'


@dataclass
class DividerBlockType(BlockType):
    @classmethod
    def get_typename(cls) -> str:
        return 'divider'


@dataclass
class EmbedBlockType(BlockType):
    url: str

    @classmethod
    def get_typename(cls) -> str:
        return 'embed'


@dataclass
class EquationBlockType(BlockType):
    expression: str
    """a KaTeX compatible string."""

    @classmethod
    def get_typename(cls) -> str:
        return 'equation'


@dataclass
class FileBlockType(BlockType):
    file: File
    caption: list[RichText] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'file'

    def serialize(self) -> dict[str, Any]:
        return {'caption': self.caption, **self.file.serialize()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized), serialized['caption'])


@dataclass
class Heading1BlockType(BlockType):
    rich_text: list[RichText]
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_1'


@dataclass
class Heading2BlockType(BlockType):
    rich_text: list[RichText]
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_2'


@dataclass
class Heading3BlockType(BlockType):
    rich_text: list[RichText]
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_3'


@dataclass
class ImageBlockType(BlockType):
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
class NumberedListItemBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'numbered_list_item'


@dataclass
class ParagraphBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'paragraph'


@dataclass
class PDFBlockType(BlockType):
    file: File
    caption: list[RichText] = field(default_factory=list)

    def serialize(self) -> dict[str, Any]:
        return {'caption': self.caption, **self.file.serialize()}

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized), serialized['caption'])

    @classmethod
    def get_typename(cls) -> str:
        return 'pdf'


@dataclass
class QuoteBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'quote'


@dataclass
class SyncedBlockType(BlockType, metaclass=ABCMeta):
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
class OriginalSyncedBlockType(SyncedBlockType):
    """cannot be changed (2023-04-02)"""
    children: list[BlockResponse] = field(default_factory=list)

    def serialize(self) -> dict[str, Any]:
        return {
            "synced_from": None,
            "children": self.children
        }


@dataclass
class DuplicatedSyncedBlockType(SyncedBlockType):
    """cannot be changed (2023-04-02)"""
    block_id: UUID

    def serialize(self) -> dict[str, Any]:
        return {'synced_from': {'block_id': self.block_id}}


@dataclass
class TableBlockType(BlockType):
    table_width: int
    """cannot be changed."""
    has_column_header: bool
    has_row_header: bool

    @classmethod
    def get_typename(cls) -> str:
        return 'table'


@dataclass
class TableRowBlockType(BlockType):
    cells: list[list[RichText]]
    """An array of cell contents in horizontal display order. Each cell is an array of rich text objects."""

    @classmethod
    def get_typename(cls) -> str:
        return 'table_row'


@dataclass
class TableOfContentsBlockType(BlockType):
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'table_of_contents'


@dataclass
class ToDoBlockType(BlockType):
    rich_text: list[RichText]
    checked: bool
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'to_do'


@dataclass
class ToggleBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockResponse] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'toggle'


@dataclass
class VideoBlockType(BlockType):
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
class UnsupportedBlockType(BlockType):
    @classmethod
    def get_typename(cls) -> str:
        return 'unsupported'
