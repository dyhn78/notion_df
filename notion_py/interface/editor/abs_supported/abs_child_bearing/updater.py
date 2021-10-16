from typing import Union

from .sphere import BlockSphere
from ..supported import SupportedBlock
from ...struct import ListEditor
from notion_py.interface.parser import BlockChildrenParser, BlockContentsParser


class BlockSphereUpdater(ListEditor):
    def __init__(self, caller: BlockSphere):
        from ...inline.unsupported import UnsupportedBlock
        super().__init__(caller)
        self.caller = caller
        self.values: list[Union[SupportedBlock, UnsupportedBlock]] = []

    def __iter__(self):
        return iter(self.values)

    def reads(self):
        return [child.fully_read for child in self]

    def reads_rich(self):
        return [child.fully_read_rich() for child in self]

    def apply_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            block_type = self.determine_block_type(child_parser)
            child = block_type(self, child_parser.block_id)
            if child.is_supported_type:
                child.contents.apply_block_parser(child_parser)
            self.values.append(child)

    @staticmethod
    def determine_block_type(child_parser: BlockContentsParser):
        if child_parser.is_supported_type:
            if not child_parser.is_page_block:
                from ...inline.text_block import TextBlock
                child = TextBlock
            else:
                from ...inline.page_block import InlinePageBlock
                child = InlinePageBlock
        else:
            from ...inline.unsupported import UnsupportedBlock
            child = UnsupportedBlock
        return child
