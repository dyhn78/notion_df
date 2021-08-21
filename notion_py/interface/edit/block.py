from .common import EditorMaster, EditorComponent
from notion_py.gateway.parse import BlockChildrenParser
from notion_py.gateway.others import GetBlockChildren


# TODO : interface.block_deprecated 가져오기.
class Block(EditorMaster):
    def __init__(self, block_id: str):
        super().__init__(block_id)
        self.children = BlockChildren(self)
        self.components.update(children=self.children)

    def fetch_children(self, page_size=0):
        requestor = GetBlockChildren(self.target_id)
        response = requestor.execute(page_size=page_size)
        children_parser = BlockChildrenParser(response)
        self.children.fetch_parser(children_parser)


class BlockChildren(EditorComponent):
    def __init__(self, caller: Block):
        super().__init__(caller)
        self.read_plain = []
        self.read_rich = []

    def fetch_parser(self, children_parser: BlockChildrenParser):
        self.read_plain = children_parser.read_plain
        self.read_rich = children_parser.read_rich
