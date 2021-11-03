from __future__ import annotations
from abc import abstractmethod, ABCMeta

from notion_py.interface.editor.common.with_children import ChildrenBearer
from notion_py.interface.editor.common.with_contents import ContentsBearer, BlockContents
from notion_py.interface.parser import BlockContentsParser


class ChildrenAndContentsBearer(ChildrenBearer, ContentsBearer):
    def __init__(self, caller):
        ChildrenBearer.__init__(self, caller)
        ContentsBearer.__init__(self, caller)

    @property
    @abstractmethod
    def contents(self) -> ChildrenBearersContents:
        pass


class ChildrenBearersContents(BlockContents, metaclass=ABCMeta):
    def __init__(self, caller: ContentsBearer, block_id: str):
        super().__init__(caller, block_id)

    def apply_block_parser(self, parser: BlockContentsParser):
        super().apply_block_parser(parser)
        self._has_children = parser.has_children
        self._can_have_children = parser.can_have_children
