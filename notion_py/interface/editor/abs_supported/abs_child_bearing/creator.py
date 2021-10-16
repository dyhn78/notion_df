from __future__ import annotations

from typing import Union

from notion_py.interface.encoder import RichTextContentsEncoder
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import AppendBlockChildren
from .sphere import BlockSphere
from ...struct import GroundEditor, PointEditor


class BlockSphereCreator(PointEditor):
    def __bool__(self):
        return bool(self.units)

    def __init__(self, caller: BlockSphere):
        super().__init__(caller)
        self.caller = caller
        self.units: list[Union[TextBlocksCreator, InlinePageBlockCreator]] = []
        self._execute_in_process = False

    def preview(self):
        res = []
        for unit in self.units:
            res.append(unit.preview())
        return res

    def execute(self):
        if self._execute_in_process:
            # message = ("child block yet not created ::\n"
            #            f"{[value.fully_read() for value in self.blocks]}")
            # raise RecursionError(message)
            return
        self._execute_in_process = True
        for unit in self.units:
            unit.execute()
        self._execute_in_process = False
        return self.blocks

    def clear(self):
        self.units = []

    @property
    def blocks(self):
        res = []
        for unit in self.units:
            res.extend(unit.blocks)
        return res

    def __iter__(self):
        return iter(self.blocks)

    def __len__(self):
        return len(self.blocks)

    def create_text_block(self):
        if self.units and isinstance(self.units[-1], TextBlocksCreator):
            unit = self.units[-1]
        else:
            unit = TextBlocksCreator(self)
            self.units.append(unit)
        return unit.add()

    def create_page_block(self):
        unit = InlinePageBlockCreator(self)
        self.units.append(unit)
        return unit


class TextBlocksCreator(GroundEditor):
    def __init__(self, caller: BlockSphereCreator):
        super().__init__(caller)
        self._requestor = AppendBlockChildren(self)

        from ...inline.text_block import TextBlock
        self.blocks: list[TextBlock] = []

    @property
    def gateway(self) -> AppendBlockChildren:
        return self._requestor

    def add(self):
        from ...inline.text_block import TextBlock
        child = TextBlock.create_new(self)
        child.contents.write_paragraph('')
        self.blocks.append(child)
        return child

    def push_carrier(self, child, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        i = self.blocks.index(child)
        return self.gateway.apply_contents(i, carrier)

    def execute(self):
        response = self.gateway.execute()
        parsers = BlockChildrenParser(response)
        for child, parser in zip(self.blocks, parsers):
            child.contents.apply_block_parser(parser)
            child.execute()


class InlinePageBlockCreator(GroundEditor):
    def __init__(self, caller: BlockSphereCreator):
        super().__init__(caller)
        self.caller = caller

        from ...inline.page_block import InlinePageBlock
        self.block = InlinePageBlock.create_new(self)

    @property
    def gateway(self):
        return self.block

    @property
    def blocks(self):
        return [self.block]
