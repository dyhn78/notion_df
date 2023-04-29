from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any

from typing_extensions import Self

from notion_df.objects.constant import BlockColor, CodeLanguage
from notion_df.objects.core import DualSerializable
from notion_df.objects.file import File
from notion_df.objects.misc import UUID, Icon
from notion_df.objects.rich_text import RichText
from notion_df.requests.block import ResponseBlock
from notion_df.utils.collection import FinalClassDict

type_object_registry: FinalClassDict[str, type[BlockType]] = FinalClassDict()


@dataclass
class BlockType(DualSerializable, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        pass

    def __init_subclass__(cls, **kwargs):
        type_object_registry[cls.get_typename()] = cls

    def serialize(self) -> dict[str, Any]:
        return self._serialize_asdict()

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(serialized)


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
    children: list[ResponseBlock] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'bulleted_list_item'


@dataclass
class CalloutBlockType(BlockType):
    rich_text: list[RichText]
    icon: Icon
    color: BlockColor = BlockColor.DEFAULT
    children: list[ResponseBlock] = field(default_factory=list)  # TODO: double check

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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized))

    @classmethod
    def get_typename(cls) -> str:
        return 'image'


@dataclass
class NumberedListItemBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[ResponseBlock] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'numbered_list_item'


@dataclass
class ParagraphBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[ResponseBlock] = field(default_factory=list)

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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized), serialized['caption'])

    @classmethod
    def get_typename(cls) -> str:
        return 'pdf'


@dataclass
class QuoteBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[ResponseBlock] = field(default_factory=list)

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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        def get_subclass():
            if serialized['synced_from']:
                return DuplicatedSyncedBlockType
            else:
                return OriginalSyncedBlockType

        return get_subclass().deserialize(serialized)


@dataclass
class OriginalSyncedBlockType(SyncedBlockType):
    """cannot be changed (2023-04-02)"""
    children: list[ResponseBlock] = field(default_factory=list)

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
    children: list[ResponseBlock] = field(default_factory=list)

    @classmethod
    def get_typename(cls) -> str:
        return 'to_do'


@dataclass
class ToggleBlockType(BlockType):
    rich_text: list[RichText]
    color: BlockColor = BlockColor.DEFAULT
    children: list[ResponseBlock] = field(default_factory=list)

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
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        return cls(File.deserialize(serialized))

    @classmethod
    def get_typename(cls) -> str:
        return 'video'


@dataclass
class UnsupportedBlockType(BlockType):
    @classmethod
    def get_typename(cls) -> str:
        return 'unsupported'
