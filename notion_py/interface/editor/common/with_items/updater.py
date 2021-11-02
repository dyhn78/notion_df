from typing import Union

from notion_py.interface.parser import BlockChildrenParser
from .bearer import ItemAttachments
from ..struct import MasterEditor
from ..struct.agents import ListEditor
from ..with_contents import ContentsBearer


class ItemsUpdater(ListEditor):
    def __init__(self, caller: ItemAttachments):
        super().__init__(caller)
        self.caller = caller
        self._values = []

    @property
    def blocks(self) -> list[Union[MasterEditor]]:
        return self._values

    def __iter__(self):
        return iter(self.blocks)

    def reads(self):
        return [child.reads for child in self]

    def reads_rich(self):
        return [child.reads_rich() for child in self]

    def apply_parser(self, children_parser: BlockChildrenParser):
        from ...inline.parser_logic import get_type_of_block_parser
        for parser in children_parser:
            block_type = get_type_of_block_parser(parser)
            child = block_type(self, parser.block_id)
            if isinstance(child, ContentsBearer):
                child.contents.apply_block_parser(parser)
            self.blocks.append(child)
