from __future__ import annotations

from typing import Union

from notion_py.interface.encoder import RichTextContentsEncoder
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import AppendBlockChildren
from .sphere import BlockSphere
from ...struct import GroundEditor, PointEditor, AdaptiveEditor


class BlockSphereCreator(PointEditor):
    def __init__(self, caller: BlockSphere):
        super().__init__(caller)
        self.caller = caller
        self.agents: list[Union[TextBlocksCreator, InlinePageBlockCreator]] = []
        self._execute_in_process = False
        self.enable_overwrite = True

    def clear(self):
        self.agents = []

    def has_updates(self):
        return bool(self.agents)

    def preview(self):
        res = []
        for unit in self.agents:
            res.append(unit.preview())
        return res

    def execute(self):
        if self._execute_in_process:
            # message = ("child block yet not created ::\n"
            #            f"{[value.fully_read() for value in self.blocks]}")
            # raise RecursionError(message)
            return []
        self._execute_in_process = True
        for agent in self.agents:
            agent.execute()
        self._execute_in_process = False
        return self.blocks

    @property
    def blocks(self):
        res = []
        for agent in self.agents:
            res.extend(agent.blocks)
        return res

    def __iter__(self):
        return iter(self.blocks)

    def __len__(self):
        return len(self.blocks)

    def create_text_block(self):
        if self.agents and isinstance(self.agents[-1], TextBlocksCreator):
            agent = self.agents[-1]
        else:
            agent = TextBlocksCreator(self)
            self.agents.append(agent)
        return agent.add()

    def create_page_block(self):
        agent = InlinePageBlockCreator(self)
        self.agents.append(agent)
        return agent.block


class TextBlocksCreator(GroundEditor):
    def __init__(self, caller: BlockSphereCreator):
        super().__init__(caller)
        self._requestor = AppendBlockChildren(self)

        from ...inline.text_block import TextBlock
        self.blocks: list[TextBlock] = []

    @property
    def requestor(self) -> AppendBlockChildren:
        return self._requestor

    def add(self):
        from ...inline.text_block import TextBlock
        child = TextBlock.create_new(self)
        self.blocks.append(child)
        self.requestor.append_space()
        child.contents.write_paragraph('')
        return child

    def push_carrier(self, child, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        i = self.blocks.index(child)
        return self.requestor.apply_contents(i, carrier)

    def execute(self):
        response = self.requestor.execute()
        parsers = BlockChildrenParser(response)
        for child, parser in zip(self.blocks, parsers):
            child.contents.apply_block_parser(parser)
            child.execute()


class InlinePageBlockCreator(AdaptiveEditor):
    def __init__(self, caller: BlockSphereCreator):
        super().__init__(caller)
        self.caller = caller

        from ...inline.page_block import InlinePageBlock
        self.block = InlinePageBlock.create_new(self)

    @property
    def value(self):
        return self.block

    @property
    def blocks(self):
        return [self.block]
