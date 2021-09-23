from typing import Union, Optional

from notion_py.interface.api_encode import PageContentsWriterAsChild, \
    RichTextContentsEncoder
from notion_py.interface.api_parse import PageParser
from notion_py.interface.gateway import UpdatePage, RetrievePage, AppendBlockChildren
from notion_py.interface.struct import Editor, PointEditor, drop_empty_request
from ..abs_supported.abs_child_bearing.abs_contents_bearing.master import \
    ContentsBearingBlock, BlockContents
from ..abs_supported.abs_child_bearing.creater_page_as_child import \
    BlockSphereCreatorWithChildInlinePage


class InlinePageBlockAsChild(ContentsBearingBlock):
    def __init__(self, caller: Union[Editor, PointEditor], page_id: str):
        super().__init__(caller, page_id)
        if isinstance(caller, BlockSphereCreatorWithChildInlinePage):
            self.contents = PageContentsAsChild(self, caller)
        else:
            self.contents = PageContentsAsChild(self)
        self.agents.update(contents=self.contents)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    @drop_empty_request
    def execute(self):
        if self.yet_not_created:
            self.caller.execute()
        else:
            self.contents.execute()
            self.sphere.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='page')

    def fully_read_rich(self):
        return dict(**super().fully_read_rich(), type='page')


class PageContentsAsChild(BlockContents, PageContentsWriterAsChild):
    def __init__(self, caller: PointEditor,
                 uncle: Optional[BlockSphereCreatorWithChildInlinePage] = None):
        super().__init__(caller)
        self.caller = caller
        if self.yet_not_created:
            gateway = uncle.gateway
        else:
            gateway = UpdatePage(self)
        self.gateway: Union[AppendBlockChildren, UpdatePage] = gateway

    def archive(self):
        self.gateway.archive()

    def un_archive(self):
        self.gateway.un_archive()

    def retrieve(self):
        gateway = RetrievePage(self)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self.yet_not_created:
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
            self.gateway = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
        self.caller.title = parser.title
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def push_carrier(self, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        if self.yet_not_created:
            return self.gateway.apply_contents(carrier)
        else:
            return self.gateway.apply_prop(carrier)
