from __future__ import annotations

from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import cast, Any, Optional, TYPE_CHECKING
from uuid import UUID

from typing_extensions import Self

from notion_df.core.collection import FinalDict
from notion_df.core.serialization import DualSerializable
from notion_df.constant import BlockColor, CodeLanguage
from notion_df.file import File
from notion_df.misc import Icon
from notion_df.rich_text import RichText, Span

if TYPE_CHECKING:
    from notion_df.data import BlockData

block_contents_registry: FinalDict[str, type[BlockContents]] = FinalDict()


@dataclass
class BlockContents(DualSerializable, metaclass=ABCMeta):
    @classmethod
    @abstractmethod
    def get_typename(cls) -> str:
        return ''

    def __init_subclass__(cls, **kwargs):
        if (typename := cls.get_typename()) and typename != cast(cls, super(cls, cls)).get_typename():
            block_contents_registry[typename] = cls

    def serialize(self) -> dict[str, Any]:
        return self._serialize_as_dict()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(raw)


def serialize_block_contents_list(block_contents_list: Optional[list[BlockContents]]) -> Optional[list[dict[str, Any]]]:
    if block_contents_list is None:
        return None
    return [{
        "object": "block",
        "type": block_type.get_typename(),
        block_type.get_typename(): block_type.serialize(),
    } for block_type in block_contents_list]


@dataclass
class BookmarkBlockContents(BlockContents):
    url: str
    caption: RichText = field(default_factory=RichText)

    @classmethod
    def get_typename(cls) -> str:
        return 'bookmark'


@dataclass
class BreadcrumbBlockContents(BlockContents):
    @classmethod
    def get_typename(cls) -> str:
        return 'breadcrumb'


@dataclass
class BulletedListItemBlockContents(BlockContents):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'bulleted_list_item'


@dataclass
class CalloutBlockContents(BlockContents):
    rich_text: RichText
    icon: Icon
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'callout'


@dataclass
class ChildDatabaseBlockContents(BlockContents):
    title: str

    @classmethod
    def get_typename(cls) -> str:
        return 'child_database'


@dataclass
class ChildPageBlockContents(BlockContents):
    title: str

    @classmethod
    def get_typename(cls) -> str:
        return 'child_page'


@dataclass
class CodeBlockContents(BlockContents):
    rich_text: RichText
    language: CodeLanguage = CodeLanguage.PLAIN_TEXT
    caption: RichText = field(default_factory=RichText)

    @classmethod
    def get_typename(cls) -> str:
        return 'code'


@dataclass
class ColumnListBlockContents(BlockContents):
    @classmethod
    def get_typename(cls) -> str:
        return 'column_list'


@dataclass
class ColumnBlockContents(BlockContents):
    @classmethod
    def get_typename(cls) -> str:
        return 'column'


@dataclass
class DividerBlockContents(BlockContents):
    @classmethod
    def get_typename(cls) -> str:
        return 'divider'


@dataclass
class EmbedBlockContents(BlockContents):
    url: str

    @classmethod
    def get_typename(cls) -> str:
        return 'embed'


@dataclass
class EquationBlockContents(BlockContents):
    expression: str
    """a KaTeX compatible string."""

    @classmethod
    def get_typename(cls) -> str:
        return 'equation'


@dataclass
class FileBlockContents(BlockContents):
    file: File
    caption: RichText = field(default_factory=RichText)

    @classmethod
    def get_typename(cls) -> str:
        return 'file'

    def serialize(self) -> dict[str, Any]:
        return {'caption': self.caption, **self.file.serialize()}

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(File.deserialize(raw), raw['caption'])


@dataclass
class Heading1BlockContents(BlockContents):
    rich_text: RichText
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_1'


@dataclass
class Heading2BlockContents(BlockContents):
    rich_text: RichText
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_2'


@dataclass
class Heading3BlockContents(BlockContents):
    rich_text: RichText
    is_toggleable: bool
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'heading_3'


@dataclass
class ImageBlockContents(BlockContents):
    """
    - The image must be directly hosted. In other words, the url cannot point to a service that retrieves the image.
    - supported image types (as of 2023-04-02): **.bmp .gif .heic .jpeg .jpg .png .svg .tif .tiff**
    https://developers.notion.com/reference/block#image
    """
    file: File

    def serialize(self) -> dict[str, Any]:
        return self.file.serialize()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(File.deserialize(raw))

    @classmethod
    def get_typename(cls) -> str:
        return 'image'


@dataclass
class NumberedListItemBlockContents(BlockContents):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'numbered_list_item'


@dataclass
class ParagraphBlockContents(BlockContents):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'paragraph'


@dataclass
class PDFBlockContents(BlockContents):
    file: File
    caption: RichText = field(default_factory=RichText)

    def serialize(self) -> dict[str, Any]:
        return {'caption': self.caption, **self.file.serialize()}

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(File.deserialize(raw), raw['caption'])

    @classmethod
    def get_typename(cls) -> str:
        return 'pdf'


@dataclass
class QuoteBlockContents(BlockContents):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'quote'


@dataclass
class SyncedBlockContents(BlockContents, metaclass=ABCMeta):
    """cannot be changed (2023-04-02)"""

    @classmethod
    def get_typename(cls) -> str:
        return 'synced_block'

    @classmethod
    def _deserialize_subclass(cls, raw: dict[str, Any]) -> Self:
        def get_subclass():
            if raw['synced_from']:
                return DuplicatedSyncedBlockValue
            else:
                return OriginalSyncedBlockValue

        return get_subclass().deserialize(raw)


@dataclass
class OriginalSyncedBlockValue(SyncedBlockContents):
    """cannot be changed (2023-04-02)"""
    children: list[BlockData] = field(init=False, default=None)

    def serialize(self) -> dict[str, Any]:
        return {
            "synced_from": None,
            "children": self.children
        }


@dataclass
class DuplicatedSyncedBlockValue(SyncedBlockContents):
    """cannot be changed (2023-04-02)"""
    block_id: UUID

    def serialize(self) -> dict[str, Any]:
        return {'synced_from': {'block_id': str(self.block_id)}}

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(block_id=UUID(raw["synced_from"]["block_id"]))


@dataclass
class TableBlockContents(BlockContents):
    table_width: int
    """cannot be changed."""
    has_column_header: bool
    has_row_header: bool

    @classmethod
    def get_typename(cls) -> str:
        return 'table'


@dataclass
class TableRowBlockContents(BlockContents):
    cells: list[list[Span]]
    """An array of cell data in horizontal display order. Each cell is an array of rich text objects."""

    @classmethod
    def get_typename(cls) -> str:
        return 'table_row'


@dataclass
class TableOfContentsBlockContents(BlockContents):
    color: BlockColor = BlockColor.DEFAULT

    @classmethod
    def get_typename(cls) -> str:
        return 'table_of_contents'


@dataclass
class ToDoBlockContents(BlockContents):
    rich_text: RichText
    checked: bool
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'to_do'


@dataclass
class ToggleBlockContents(BlockContents):
    rich_text: RichText
    color: BlockColor = BlockColor.DEFAULT
    children: list[BlockData] = field(init=False, default=None)

    @classmethod
    def get_typename(cls) -> str:
        return 'toggle'


@dataclass
class VideoBlockContents(BlockContents):
    """
    supported video types (as 2023-04-02):
    **.amv .asf .avi .f4v .flv .gifv .mkv .mov .mpg .mpeg .mpv .mp4 .m4v .qt .wmv**

    https://developers.notion.com/reference/block#supported-video-types
    """
    file: File

    def serialize(self) -> dict[str, Any]:
        return self.file.serialize()

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(File.deserialize(raw))

    @classmethod
    def get_typename(cls) -> str:
        return 'video'


@dataclass
class UnsupportedBlockContents(BlockContents):
    @classmethod
    def get_typename(cls) -> str:
        return 'unsupported'
