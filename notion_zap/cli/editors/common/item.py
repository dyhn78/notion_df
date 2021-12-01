from __future__ import annotations

from abc import ABCMeta
from abc import abstractmethod
from typing import Union

from notion_zap.cli.gateway import parsers
from .with_items.leaders import ItemsBearer, ItemChildren
from ..structs.exceptions import InvalidParentTypeError, NoParentFoundError
from ..structs.followers import RequestEditor
from ..structs.leaders import Block, Payload
from ..structs.leaders import Root


class Item(Block, metaclass=ABCMeta):
    def __init__(self, caller: Union[ItemChildren, Root], id_or_url: str):
        super().__init__(caller, id_or_url)

    @property
    def is_supported_type(self) -> bool:
        return True

    @property
    def payload(self) -> ItemContents:
        return self.contents

    @property
    @abstractmethod
    def contents(self) -> ItemContents:
        pass

    @property
    def parent(self):
        if parent := self.parent:
            if not isinstance(parent, ItemsBearer):
                raise InvalidParentTypeError(self)
            return parent
        return None

    def exdent_cursor(self):
        """this returns new 'cursor' where you can use of open_new_xx method.
        raises NoParentFoundError if the page is directly called from root."""
        if parent := self.parent:
            return parent.children
        else:
            raise NoParentFoundError(self.block)


class ItemContents(Payload, RequestEditor, metaclass=ABCMeta):
    def __init__(self, caller: Item):
        Payload.__init__(self, caller)
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
        self._has_children = parser.has_children
        self._can_have_children = parser.can_have_children
