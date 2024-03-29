from __future__ import annotations

from abc import ABCMeta
from typing import Union, Optional, Hashable

from notion_zap.cli.core.exceptions import NoParentFoundError
from notion_zap.cli.gateway import parsers
from .with_items.with_items import BlockWithItems, ItemChildren
from ...core.base import Block, RootSpace


class Item(Block, metaclass=ABCMeta):
    def __init__(self, caller: Union[ItemChildren, RootSpace], id_or_url: str,
                 alias: Hashable = None):
        self._read_plain = ''
        self._read_rich = []
        super().__init__(caller, id_or_url, alias)

    @property
    def is_supported_type(self) -> bool:
        return True

    def read_contents(self) -> str:
        return self._read_plain

    def richly_read_contents(self) -> list:
        return self._read_rich

    def apply_block_parser(self, parser: parsers.BlockParser):
        self._regs.un_register_from_root_and_parent()
        self._apply_block_parser(parser)
        self._regs.register_to_root_and_parent()

    def _apply_block_parser(self, parser: parsers.BlockParser):
        self._block_id = parser.block_id
        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich
        self._created_time = parser.created_time
        self._last_edited_time = parser.last_edited_time
        self._has_children = parser.has_children
        self._can_have_children = parser.can_have_children

    @property
    def parent(self) -> Optional[BlockWithItems]:
        return super().parent

    def exdent_cursor(self):
        """this returns new 'cursor' where you can use of open_new_xx method.
        raises NoParentFoundError if the page is directly called from root."""
        if parent := self.parent:
            return parent.children
        else:
            raise NoParentFoundError(self.block)
