from abc import ABCMeta
from typing import Optional

from notion_py.interface.editor.common.struct import Editor
from notion_py.interface.editor.common.struct.agents import GroundEditor
from notion_py.interface.editor.common.supported import SupportedBlock
from notion_py.interface.parser import BlockContentsParser


class ContentsBearer(SupportedBlock, metaclass=ABCMeta):
    def __init__(self, caller: Editor, block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller
        self.contents: Optional[BlockContents] = None

    @property
    def payload(self):
        return self.contents

    def reads(self):
        return {'contents': self.contents.reads()}

    def reads_rich(self):
        return {'contents': self.contents.reads_rich()}

    def save_info(self):
        return {'contents': self.contents.save_info()}


class BlockContents(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: ContentsBearer):
        super().__init__(caller)
        self.caller = caller
        self._read_plain = ''
        self._read_rich = []

    def reads(self) -> str:
        return self._read_plain

    def reads_rich(self) -> list:
        return self._read_rich

    def apply_block_parser(self, parser: BlockContentsParser):
        if parser.block_id:
            self.master_id = parser.block_id
            self.yet_not_created = False
        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich
