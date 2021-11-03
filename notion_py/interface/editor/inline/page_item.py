from __future__ import annotations

from typing import Union

from notion_py.interface.encoder import (
    PageContentsWriter, RichTextPropertyEncoder)
from notion_py.interface.parser import PageParser
from notion_py.interface.requestor import CreatePage, UpdatePage
from notion_py.interface.utility import eval_empty
from ..common.pages import PageBlock, PagePayload
from ..common.with_cc import ChildrenAndContentsBearer, ChildrenBearersContents
from ..common.with_items import ItemsUpdater, PageItemCreateAgent
from ..root_editor import RootEditor


class PageItem(PageBlock, ChildrenAndContentsBearer):
    def __init__(self,
                 caller: Union[RootEditor,
                               ItemsUpdater,
                               PageItemCreateAgent],
                 page_id: str):
        PageBlock.__init__(self, caller)
        ChildrenAndContentsBearer.__init__(self, caller)
        self.caller = caller
        self._contents = PageItemContents(self, page_id)

    @property
    def payload(self) -> PageItemContents:
        return self.contents

    @property
    def contents(self) -> PageItemContents:
        return self._contents

    @property
    def block_name(self):
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


class PageItemContents(PagePayload, ChildrenBearersContents, PageContentsWriter):
    def __init__(self, caller: PageItem, page_id: str):
        super().__init__(caller, page_id)
        self.caller = caller
        if self.yet_not_created:
            requestor = CreatePage(self, under_database=False)
        else:
            requestor = UpdatePage(self)
        self._requestor = requestor

    @property
    def requestor(self) -> Union[UpdatePage, CreatePage]:
        return self._requestor

    def clear_requestor(self):
        if self.yet_not_created:
            self._requestor = CreatePage(self, under_database=False)
        else:
            self._requestor = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        super().apply_page_parser(parser)
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def push_carrier(self, carrier: RichTextPropertyEncoder) \
            -> RichTextPropertyEncoder:
        writeable = self.root.enable_overwrite or eval_empty(self.reads())
        if not writeable:
            return carrier
        ret = self.requestor.apply_prop(carrier)
        # this is always title
        self._set_title(carrier.plain_form())
        return ret
