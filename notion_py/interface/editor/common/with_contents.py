from __future__ import annotations
from abc import ABCMeta, abstractmethod

from notion_py.interface.parser import BlockContentsParser
from .struct import Editor, GroundEditor
from .supported import SupportedBlock
from .with_children import ChildrenBearer


class ContentsBearer(SupportedBlock, metaclass=ABCMeta):
    def __init__(self, caller: Editor, block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller

    @property
    def payload(self):
        return self.contents

    @property
    @abstractmethod
    def contents(self) -> BlockContents:
        pass

    @contents.setter
    @abstractmethod
    def contents(self, value):
        pass

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
        master = self.master
        if isinstance(master, ChildrenBearer):
            master.has_children = parser.has_children
