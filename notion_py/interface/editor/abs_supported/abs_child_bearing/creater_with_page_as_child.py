from ...struct import GroundEditor, PointEditor
from notion_py.interface.encoder import RichTextContentsEncoder
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import AppendBlockChildren


class BlockSphereCreatorWithChildInlinePage(GroundEditor):
    def __init__(self, caller: PointEditor):
        from .abs_contents_bearing.master import ContentsBearingBlock
        super().__init__(caller)
        self.caller = caller
        self.values: list[ContentsBearingBlock] = []
        self.gateway = AppendBlockChildren(self)
        self._chunk_interrupted = True

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any(child for child in self)

    def execute(self):
        response = self.gateway.execute()
        parsers = BlockChildrenParser(response)
        for parser, new_child in zip(parsers, self.values):
            new_child.contents.apply_block_parser(parser)
        for child in self.values:
            child.execute()
        res = self.values.copy()
        self.values.clear()
        return res

    def create_text_block(self):
        from ...inline.text_block import TextBlock
        child = TextBlock.create_new(self)
        self.values.append(child)
        assert id(child) == id(self[-1])
        return child

    def create_inline_page(self):
        from ...inline.page_block_as_child import InlinePageBlockAsChild
        child = InlinePageBlockAsChild.create_new(self)
        self.values.append(child)
        assert id(child) == id(self[-1])
        return child

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)
