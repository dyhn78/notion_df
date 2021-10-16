from typing import Union, Optional

from notion_py.interface.encoder import PageContentsWriter, \
    RichTextPropertyEncoder
from notion_py.interface.parser import PageParser
from notion_py.interface.requestor import \
    CreatePage, UpdatePage
from notion_py.interface.utility import eval_empty
from ..abs_page_property import PageProperty
from ..abs_supported.abs_child_bearing.abs_contents_bearing.contents_bearing import \
    ContentsBearingBlock, BlockContents
from ..abs_supported.abs_child_bearing.creator import BlockSphereCreator
from ..abs_supported.abs_child_bearing.updater import BlockSphereUpdater
from ...common.struct import drop_empty_request, Editor


class InlinePageBlock(ContentsBearingBlock):
    def __init__(self,
                 caller: Union[Editor,
                               BlockSphereUpdater,
                               BlockSphereCreator],
                 page_id: str):
        super().__init__(caller, page_id)
        self.caller = caller
        if isinstance(caller, BlockSphereCreator):
            self.yet_not_created = True
        self.contents = InlinePageContents(self)
        self.agents.update(contents=self.contents)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    @drop_empty_request
    def execute(self):
        self.contents.execute()
        if self.archived:
            return
        self.sphere.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='page')

    def fully_read_rich(self):
        return dict(**super().fully_read_rich(), type='page')


class InlinePageContents(PageProperty, BlockContents, PageContentsWriter):
    def __init__(self, caller: InlinePageBlock):
        super().__init__(caller)
        self.caller = caller
        if self.yet_not_created:
            requestor = CreatePage(self, under_database=False)
        else:
            requestor = UpdatePage(self)
        self._requestor = requestor

    @property
    def gateway(self) -> Union[UpdatePage, CreatePage]:
        return self._requestor

    @gateway.setter
    def gateway(self, value):
        self._requestor = value

    def apply_page_parser(self, parser: PageParser):
        super().apply_page_parser(parser)
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def push_carrier(self, carrier: RichTextPropertyEncoder) \
            -> Optional[RichTextPropertyEncoder]:
        overwrite = self.enable_overwrite or eval_empty(self.read())
        if overwrite:
            return self.gateway.apply_prop(carrier)
        else:
            return carrier
