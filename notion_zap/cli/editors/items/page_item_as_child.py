# from typing import Union, Optional
#
# from notion_zap.gateway.encoders import PageContentsWriterAsChild, \
#     RichTextContentsEncoder
# from notion_zap.gateway.parsers import PageParser
# from notion_zap.gateway.requestors import UpdatePage, RetrievePage, AppendBlockChildren
# from notion_zap.gateway.base.base import GeneralEditor, drop_empty_request
# from ..supported.with_items.with_contents.contents_bearing import \
#     ContentsBearer, BlockContents
# from ..supported.with_items.creater_with_page_as_child import \
#     BlockSphereCreatorWithChildInlinePage
# from ..base import GeneralEditor
#
#
# class InlinePageBlockAsChild(ContentsBearer):
#     def __init__(self, caller: Union[GeneralEditor, GeneralEditor], page_id: str):
#         super().__init__(caller, page_id)
#         if isinstance(caller, BlockSphereCreatorWithChildInlinePage):
#             self.contents = InlinePageContentsAsChild(self, caller)
#         else:
#             self.contents = InlinePageContentsAsChild(self)
#         self.agents.update(contents=self.contents)
#         self.title = ''
#
#     @property
#     def block_name(self):
#         return self.title
#
#     @drop_empty_request
#     def execute(self):
#         if self.yet_not_created:
#             self.caller.execute()
#         else:
#             self.contents.execute()
#             self.items.execute()
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
#             requestors = uncle.requestors
#         else:
#             requestors = UpdatePage(self)
#         self.requestors: Union[AppendBlockChildren, UpdatePage] = requestors
#
#     def archive(self):
#         self.requestors.archive()
#
#     def un_archive(self):
#         self.requestors.un_archive()
#
#     def retrieve(self):
#         requestors = RetrievePage(self)
#         response = requestors.execute()
#         parsers = PageParser.parse_retrieve(response)
#         self.apply_page_parser(parsers)
#
#     def execute(self):
#         response = self.requestors.execute()
#         if self.yet_not_created:
#             parsers = PageParser.parse_create(response)
#             self.apply_page_parser(parsers)
#             self.requestors = UpdatePage(self)
#
#     def apply_page_parser(self, parsers: PageParser):
#         if parsers.page_id:
#             self.block_id = parsers.page_id
#         self.caller.title = parsers.title
#         self._read_plain = parsers.prop_values['title']
#         self._read_rich = parsers.prop_rich_values['title']
#
#     def push_carrier(self, carrier: RichTextContentsEncoder) \
#             -> RichTextContentsEncoder:
#         if self.yet_not_created:
#             return self.requestors.apply_contents(, carrier
#         else:
#             return self.requestors.apply_prop(carrier)
