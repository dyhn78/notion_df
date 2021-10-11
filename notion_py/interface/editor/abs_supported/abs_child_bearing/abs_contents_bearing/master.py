from abc import ABCMeta, abstractmethod
from typing import Union, Optional

from notion_py.interface.common.struct import Editor
from notion_py.interface.editor.struct import GroundEditor
from ..master import ChildBearingBlock
from notion_py.interface.parser import BlockContentsParser
from notion_py.interface.requestor import UpdateBlock, UpdatePage, CreatePage


class ContentsBearingBlock(ChildBearingBlock, metaclass=ABCMeta):
    def __init__(self, caller: Editor, block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller
        self.contents: Optional[BlockContents] = None

    def fully_read(self):
        return {'contents': self.contents.read(),
                'children': self.sphere.reads()}

    def fully_read_rich(self):
        return {'contents': self.contents.read_rich(),
                'children': self.sphere.reads_rich()}

    def preview(self):
        return {'contents': self.contents.preview(),
                **self.sphere.preview()}


class BlockContents(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: ContentsBearingBlock):
        super().__init__(caller)
        self.caller = caller
        self.gateway: Union[UpdateBlock, UpdatePage, CreatePage, None] = None
        self._read_plain = ''
        self._read_rich = []

    @abstractmethod
    def retrieve(self):
        pass

    def archive(self):
        self.gateway.archive()

    def un_archive(self):
        self.gateway.un_archive()

    def apply_block_parser(self, parser: BlockContentsParser):
        if parser.block_id:
            self.master_id = parser.block_id
        self.caller.has_children = parser.has_children
        self.caller.can_have_children = parser.can_have_children
        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich

    def read(self) -> str:
        return self._read_plain

    def read_rich(self) -> list:
        return self._read_rich
