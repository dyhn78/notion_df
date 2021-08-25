from __future__ import annotations

from typing import Optional

from .editor_struct import MasterEditor, GatewayEditor, BridgeEditor
from ..parse import BlockChildrenParser, BlockChildParser
from ...gateway.read import GetBlockChildren
from ...gateway.write import UpdateBlock


class Block(MasterEditor):
    def __init__(self, block_id: str, caller: Optional[BridgeEditor] = None):
        super().__init__(block_id, caller=caller)
        self.children = BlockChildren(self)
        self.agents.update(children=BlockChildren(self))
        self.can_have_children = True

    def fetch_children(self, page_size=0):
        requestor = GetBlockChildren(self.master_id)
        response = requestor.execute(page_size=page_size)
        parser = BlockChildrenParser(response)
        self.children.fetch_parser(parser)

    def fetch_descendants(self, page_size=0):
        self.fetch_children(page_size)
        for child in self.children:
            if not child.can_have_children:
                continue
            child.fetch_descendants()


class BlockChildren(BridgeEditor):
    def __init__(self, caller: Block):
        super().__init__(caller)
        self.values: list[InlineBlock] = []

    def __iter__(self) -> list[InlineBlock]:
        return self.values

    def fetch_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            child = InlineBlock(child_parser.block_id)
            child.contents.fetch_parser(child_parser)
            self.values.append(child)

    def read_plain(self):
        return [child.contents.read_plain for child in self]

    def read_rich(self):
        return [child.contents.read_rich for child in self]


class InlineBlock(Block):
    def __init__(self, block_id: str, caller: Optional[BridgeEditor] = None):
        super().__init__(block_id, caller=caller)
        self.contents = InlineContents(self)
        self.agents.update(contents=self.contents)


class InlineContents(GatewayEditor):
    def __init__(self, caller: InlineBlock):
        super().__init__(caller)
        self.gateway = UpdateBlock(self.caller.master_id)
        self.read_plain = ''
        self.read_rich = []

    def fetch_parser(self, child_parser: BlockChildParser):
        self.read_plain = child_parser.read_plain
        self.read_rich = child_parser.read_rich
        self.caller.can_have_children = child_parser.can_have_children

    def write(self, value):
        pass  # TODO

    def write_rich(self):
        pass
