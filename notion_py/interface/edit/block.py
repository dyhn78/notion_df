from .common import EditorMaster, EditorComponent
from ..parse import BlockChildrenParser
from notion_py.gateway.others import GetBlockChildren


class Block(EditorMaster):
    def __init__(self, head_id: str):
        super().__init__(head_id)
        self.children = None

    def fetch_children(self, page_size=0):
        requestor = GetBlockChildren(self.head_id)
        response = requestor.execute(page_size=page_size)
        children_parser = BlockChildrenParser(response)
        self.children = BlockChildren(caller=self,
                                      read_plain=children_parser.read_plain,
                                      read_rich=children_parser.read_rich)
        self.components.update(children=self.children)
        # TODO


class BlockChildren(EditorComponent):
    def __init__(self, caller: Block,
                 read_plain: list[str], read_rich: list[list]):
        super().__init__(caller)
        self.read_plain = read_plain
        self.read_rich = read_rich
