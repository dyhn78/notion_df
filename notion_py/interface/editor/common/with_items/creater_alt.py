# from typing import Union
#
# from notion_py.interface.common.struct import Requestor
# from ...struct import GroundEditor, BlockEditor
# from notion_py.interface.encoder import RichTextContentsEncoder
# from notion_py.interface.parser import BlockChildrenParser
# from notion_py.interface.requestor import AppendBlockChildren
#
#
# class BlockSphereCreatorWithChildInlinePage(GroundEditor):
#     def __init__(self, caller: BlockEditor):
#         requestor = AppendBlockChildren(self)
#         super().__init__(caller)
#         self.caller = caller
#         self.requestor = requestor
#         from .with_contents.contents_bearing import ContentsBearer
#         self.blocks: list[ContentsBearer] = []
#         self._chunk_interrupted = True
#
#     def __iter__(self):
#         return iter(self.blocks)
#
#     def __getitem__(self, index: int):
#         return self.blocks[index]
#
#     def __len__(self):
#         return len(self.blocks)
#
#     def __bool__(self):
#         return any(child for child in self)
#
#     @property
#     def gateway(self):
#         return self.requestor
#
#     def execute(self):
#         response = self.gateway.execute()
#         parsers = BlockChildrenParser(response)
#         for parser, new_child in zip(parsers, self.blocks):
#             new_child.contents.apply_block_parser(parser)
#         for child in self.blocks:
#             child.execute()
#         res = self.blocks.copy()
#         self.blocks.clear()
#         return res
#
#     def create_text_block(self):
#         from ...inline.text_block import TextItem
#         child = TextItem.create_new(self)
#         self.blocks.append(child)
#         assert id(child) == id(self[-1])
#         return child
#
#     def create_inline_page(self):
#         from ...inline.page_block_as_child import InlinePageBlockAsChild
#         child = InlinePageBlockAsChild.create_new(self)
#         self.blocks.append(child)
#         assert id(child) == id(self[-1])
#         return child
#
#     def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
#         return self.gateway.apply_contents()
