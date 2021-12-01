from __future__ import annotations

from abc import ABCMeta, abstractmethod

from ..structs.leaders import Block, Payload
from ..structs.followers import RequestEditor
from notion_zap.cli.gateway import parsers


class ContentsBearer(Block, metaclass=ABCMeta):
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

    def read(self):
        return dict(**super().read(),
                    contents=self.contents.read())

    def richly_read(self):
        return dict(**super().richly_read(),
                    contents=self.contents.richly_read())

    def save_info(self):
        return dict(**super().save_info(),
                    contents=self.contents.save_info())


class BlockContents(Payload, RequestEditor, metaclass=ABCMeta):
    def __init__(self, caller: ContentsBearer, id_or_url: str):
        Payload.__init__(self, caller, id_or_url)
        self.caller = caller
        self._read_plain = ''
        self._read_rich = []

    def read(self) -> str:
        return self._read_plain

    def richly_read(self) -> list:
        return self._read_rich

    def apply_block_parser(self, parser: parsers.BlockContentsParser):
        if parser.block_id:
            self._set_block_id(parser.block_id)
        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich
        self._created_time = parser.created_time
        self._last_edited_time = parser.last_edited_time
