from __future__ import annotations

from typing import Optional

from .editor_struct import MasterEditor, GatewayEditor, BridgeEditor
from ..encode.block_contents import BlockContents
from ..encode.block_unit import BlockWriter
from ..parse import BlockChildrenParser, BlockContentsParser
from ...gateway.read import GetBlockChildren, RetrieveBlock
from ...gateway.write import UpdateBlock, AppendBlockChildren


class Block(MasterEditor):
    def __init__(self, block_id: str, caller: Optional[BridgeEditor] = None):
        super().__init__(block_id, caller=caller)
        self.children = BlockChildren(self)
        self.agents.update(children=BlockChildren(self))
        self.has_children = True
        self.can_have_children = True

    def fetch_children(self, page_size=0):
        gateway = GetBlockChildren(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = BlockChildrenParser(response)
        self.children.fetch_parser(parser)

    def fetch_descendants(self, page_size=0):
        self.fetch_children(page_size)
        for child in self.children:
            if child.has_children:
                child.fetch_descendants()


class BlockChildren(BridgeEditor, GatewayEditor, BlockContents):
    def __init__(self, caller: Block):
        BridgeEditor.__init__(self, caller)
        self.values: list[InlineBlock] = []
        self.gateway = AppendBlockChildren(self.caller.master_id)
        self.new_values: list[InlineBlock] = []

    def __iter__(self) -> list[InlineBlock]:
        return self.values + self.new_values

    def fetch_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            child = InlineBlock(child_parser.block_id)
            child.contents.fetch_parser(child_parser)
            self.values.append(child)

    def read_plain(self):
        return [child.contents.read_plain for child in self]

    def read_rich(self):
        return [child.contents.read_rich for child in self]

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        self.new_values.append(InlineBlock(block_id='', caller=self))
        return self.gateway.children.apply(carrier)

    def execute(self):
        response = BridgeEditor.execute(self)
        for response_frag, new_value in zip(response, self.new_values):
            new_value.fetch_execution_result(response_frag)
            self.values.append(new_value)
        self.new_values = []


class InlineBlock(Block):
    def __init__(self, block_id: str, caller: Optional[BridgeEditor] = None):
        super().__init__(block_id, caller=caller)
        self.contents = InlineContents(self)
        self.agents.update(contents=self.contents)

    def fetch_retrieve(self):
        gateway = RetrieveBlock(self.master_id)
        response = gateway.execute()
        parser = BlockContentsParser.fetch_response_frag(response)
        self.contents.fetch_parser(parser)

    def fetch_execution_result(self, response: dict):
        parser = BlockContentsParser.fetch_response_frag(response)
        self.contents.fetch_parser(parser)


class InlineContents(GatewayEditor, BlockContents):
    def __init__(self, caller: InlineBlock):
        GatewayEditor.__init__(self, caller)
        self.gateway = UpdateBlock(self.caller.master_id)
        self.read_plain = ''
        self.read_rich = []

    def fetch_parser(self, child_parser: BlockContentsParser):
        self.read_plain = child_parser.read_plain
        self.read_rich = child_parser.read_rich
        self.caller.has_children = child_parser.has_children
        self.caller.can_have_children = child_parser.can_have_children

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        self.gateway.contents = carrier
        return carrier
