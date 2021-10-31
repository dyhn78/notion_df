from typing import Union

from notion_py.interface.encoder import (
    PageContentsWriter, RichTextPropertyEncoder)
from notion_py.interface.parser import PageParser
from notion_py.interface.requestor import CreatePage, UpdatePage
from notion_py.interface.utility import eval_empty
from ..common.pages import PageBlock, PagePayload
from ..common.with_contents import ContentsBearer, BlockContents
from ..common.with_items import ItemsUpdater, PageItemCreateAgent
from ..root_editor import RootEditor


class PageItem(PageBlock, ContentsBearer):
    def __init__(self,
                 caller: Union[RootEditor,
                               ItemsUpdater,
                               PageItemCreateAgent],
                 page_id: str,
                 yet_not_created=False):
        super().__init__(caller, page_id)
        self.caller = caller
        self.yet_not_created = yet_not_created
        self.contents = PageItemContents(self)

    @property
    def payload(self):
        return self.contents

    @classmethod
    def create_new(cls, caller: PageItemCreateAgent):
        self = cls(caller, '', yet_not_created=True)
        return self

    @property
    def master_name(self):
        return self.title

    def save(self):
        self.contents.save()
        if self.archived:
            return
        self.attachments.save()

    def reads(self):
        return dict(**super().reads(), type='page')

    def reads_rich(self):
        return dict(**super().reads_rich(), type='page')


class PageItemContents(PagePayload, BlockContents, PageContentsWriter):
    def __init__(self, caller: PageItem):
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
            -> RichTextPropertyEncoder:
        overwrite = self.root.enable_overwrite or eval_empty(self.reads())
        if overwrite:
            return self.requestor.apply_prop(carrier)
        else:
            return carrier
