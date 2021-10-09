from typing import Union, Optional

from notion_py.interface.api_encode import PageContentsWriterAsIndep, \
    RichTextPropertyEncoder
from notion_py.interface.api_parse import PageParser

from ..abs_supported.abs_child_bearing.abs_contents_bearing.master import \
    ContentsBearingBlock, BlockContents
from notion_py.interface.gateway import CreatePage, UpdatePage, RetrievePage
from notion_py.interface.struct import Editor, PointEditor, drop_empty_request
from notion_py.interface.utility import eval_empty


class InlinePageBlock(ContentsBearingBlock):
    def __init__(self, caller: Union[Editor, PointEditor], page_id: str):
        super().__init__(caller, page_id)
        self.contents = InlinePageContents(self)
        self.agents.update(contents=self.contents)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    @drop_empty_request
    def execute(self):
        self.contents.execute()
        if not self.archived:
            self.sphere.execute()
        self.sphere.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='page')

    def fully_read_rich(self):
        return dict(**super().fully_read_rich(), type='page')


class InlinePageContents(BlockContents, PageContentsWriterAsIndep):
    def __init__(self, caller: PointEditor):
        super().__init__(caller)
        self.caller = caller
        if not self.yet_not_created:
            gateway = UpdatePage(self)
        else:
            gateway = CreatePage(self, under_database=False)
        self.gateway = gateway

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
        else:
            pass
            # TODO: update {self._read};
            #  consider making PageParser yourself without response

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
        self.caller.title = parser.title
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def push_carrier(self, carrier: RichTextPropertyEncoder) \
            -> Optional[RichTextPropertyEncoder]:
        overwrite = self.enable_overwrite or eval_empty(self.read())
        if overwrite:
            return self.gateway.apply_prop(carrier)
        else:
            return carrier
