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
from ..abs_supported.abs_child_bearing.creator import InlinePageBlockCreator
from ..abs_supported.abs_child_bearing.updater import BlockSphereUpdater
from ...common.struct import Editor


class InlinePageBlock(ContentsBearingBlock):
    def __init__(self,
                 caller: Union[Editor,
                               BlockSphereUpdater,
                               InlinePageBlockCreator],
                 page_id: str):
        super().__init__(caller, page_id)
        self.caller = caller
        if isinstance(caller, InlinePageBlockCreator):
            self.yet_not_created = True
        self.contents = InlinePageContents(self)
        self.agents.update(contents=self.contents)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    def execute(self):
        self.contents.execute()
        if self.archived:
            return
        self.sphere.execute()

    def reads(self):
        return dict(**super().reads(), type='page')

    def reads_rich(self):
        return dict(**super().reads_rich(), type='page')


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
    def requestor(self) -> Union[UpdatePage, CreatePage]:
        return self._requestor

    @requestor.setter
    def requestor(self, value):
        self._requestor = value

    def apply_page_parser(self, parser: PageParser):
        super().apply_page_parser(parser)
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def push_carrier(self, carrier: RichTextPropertyEncoder) \
            -> Optional[RichTextPropertyEncoder]:
        overwrite = self.root.enable_overwrite or eval_empty(self.reads())
        if overwrite:
            return self.requestor.apply_prop(carrier)
        else:
            return carrier
