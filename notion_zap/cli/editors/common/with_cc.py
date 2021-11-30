from __future__ import annotations
from abc import abstractmethod, ABCMeta

from .with_children import ChildrenBearer
from .with_contents import ContentsBearer, BlockContents
from notion_zap.cli.gateway import parsers


class ChildrenAndContentsBearer(ChildrenBearer, ContentsBearer):
    def __init__(self, caller):
        ChildrenBearer.__init__(self, caller)
        ContentsBearer.__init__(self, caller)

    @property
    @abstractmethod
    def contents(self) -> ChildrenBearersContents:
        pass


class ChildrenBearersContents(BlockContents, metaclass=ABCMeta):
    def apply_block_parser(self, parser: parsers.BlockContentsParser):
        super().apply_block_parser(parser)
        self._has_children = parser.has_children
        self._can_have_children = parser.can_have_children

