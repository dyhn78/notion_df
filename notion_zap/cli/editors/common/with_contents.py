from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Union

from notion_zap.cli.editors.root_editor import RootEditor
from ..base import MasterEditor, BlockEditor, PayloadEditor, GroundEditor
from notion_zap.cli.gateway import parsers


class ContentsBearer(MasterEditor, metaclass=ABCMeta):
    def __init__(self, caller: Union[RootEditor, BlockEditor]):
        super().__init__(caller)
        self.caller = caller

    @property
    def is_supported_type(self) -> bool:
        return True

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


class BlockContents(PayloadEditor, GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: ContentsBearer, block_id: str):
        PayloadEditor.__init__(self, caller, block_id)
        self.caller = caller
        self._read_plain = ''
        self._read_rich = []

    def reads(self) -> str:
        return self._read_plain

    def reads_rich(self) -> list:
        return self._read_rich

    def apply_block_parser(self, parser: parsers.BlockContentsParser):
        if parser.block_id:
            self._set_block_id(parser.block_id)
        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich
        self._created_time = parser.created_time
        self._last_edited_time = parser.last_edited_time
