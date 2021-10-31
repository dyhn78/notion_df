# from typing import Union, Optional
#
# from notion_py.interface.encoder import PageContentsWriterAsChild, \
#     RichTextContentsEncoder
# from notion_py.interface.parser import PageParser
# from notion_py.interface.requestor import UpdatePage, RetrievePage, AppendBlockChildren
# from notion_py.interface.common.struct import Editor, drop_empty_request
# from ..supported.with_items.with_contents.contents_bearing import \
#     ContentsBearer, BlockContents
# from ..supported.with_items.creater_with_page_as_child import \
#     BlockSphereCreatorWithChildInlinePage
# from ..struct import PointEditor
#
#
# class InlinePageBlockAsChild(ContentsBearer):
#     def __init__(self, caller: Union[Editor, PointEditor], page_id: str):
#         super().__init__(caller, page_id)
#         if isinstance(caller, BlockSphereCreatorWithChildInlinePage):
#             self.contents = InlinePageContentsAsChild(self, caller)
#         else:
#             self.contents = InlinePageContentsAsChild(self)
#         self.agents.update(contents=self.contents)
#         self.title = ''
#
#     @property
#     def master_name(self):
#         return self.title
#
#     @drop_empty_request
#     def execute(self):
#         if self.yet_not_created:
#             self.caller.execute()
#         else:
#             self.contents.execute()
#             self.attachments.execute()
#
#     def fully_read(self):
#         return dict(**super().fully_read(), type='page')
#
#     def fully_read_rich(self):
#         return dict(**super().fully_read_rich(), type='page')
#
#
# class InlinePageContentsAsChild(BlockContents, PageContentsWriterAsChild):
#     def __init__(self, caller: ContentsBearer,
#                  uncle: Optional[BlockSphereCreatorWithChildInlinePage] = None):
#         super().__init__(caller)
#         self.caller = caller
#         if self.yet_not_created:
#             requestor = uncle.requestor
#         else:
#             requestor = UpdatePage(self)
#         self.requestor: Union[AppendBlockChildren, UpdatePage] = requestor
#
#     def archive(self):
#         self.requestor.archive()
#
#     def un_archive(self):
#         self.requestor.un_archive()
#
#     def retrieve(self):
#         requestor = RetrievePage(self)
#         response = requestor.execute()
#         parser = PageParser.parse_retrieve(response)
#         self.apply_page_parser(parser)
#
#     def execute(self):
#         response = self.requestor.execute()
#         if self.yet_not_created:
#             parser = PageParser.parse_create(response)
#             self.apply_page_parser(parser)
#             self.requestor = UpdatePage(self)
#
#     def apply_page_parser(self, parser: PageParser):
#         if parser.page_id:
#             self.master_id = parser.page_id
#         self.caller.title = parser.title
#         self._read_plain = parser.prop_values['title']
#         self._read_rich = parser.prop_rich_values['title']
#
#     def push_carrier(self, carrier: RichTextContentsEncoder) \
#             -> RichTextContentsEncoder:
#         if self.yet_not_created:
#             return self.requestor.apply_contents(, carrier
#         else:
#             return self.requestor.apply_prop(carrier)
