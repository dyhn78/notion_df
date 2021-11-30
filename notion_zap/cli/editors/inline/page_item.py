from __future__ import annotations

from typing import Union

from notion_zap.cli.gateway import encoders, parsers, requestors
from ..common.pages import PageBlock, PagePayload
from ..common.with_cc import ChildrenAndContentsBearer, ChildrenBearersContents
from ..common.with_items import ItemChildren
from notion_zap.cli.editors.root_editor import RootEditor


class PageItem(PageBlock, ChildrenAndContentsBearer):
    def __init__(self,
                 caller: Union[ItemChildren, RootEditor],
                 id_or_url: str):
        PageBlock.__init__(self, caller)
        ChildrenAndContentsBearer.__init__(self, caller)
        self.caller = caller
        self._contents = PageItemContents(self, id_or_url)

    @property
    def payload(self) -> PageItemContents:
        return self._contents

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
        self.items.save()

    def reads(self):
        return dict(**super().reads(), type='page')

    def reads_rich(self):
        return dict(**super().reads_rich(), type='page')


class PageItemContents(PagePayload, ChildrenBearersContents,
                       encoders.PageContentsWriter):
    def __init__(self, caller: PageItem, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.caller = caller
        if self.yet_not_created:
            requestor = requestors.CreatePage(self, under_database=False)
        else:
            requestor = requestors.UpdatePage(self)
        self._requestor = requestor

    # @property
    # def can_have_children(self):
    #     return True

    @property
    def requestor(self):
        return self._requestor

    def clear_requestor(self):
        if self.yet_not_created:
            self._requestor = requestors.CreatePage(self, under_database=False)
        else:
            self._requestor = requestors.UpdatePage(self)

    def apply_page_parser(self, parser: parsers.PageParser):
        super().apply_page_parser(parser)
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']
        self._set_title(self._read_plain)

    def apply_block_parser(self, parser: parsers.BlockContentsParser):
        super().apply_block_parser(parser)
        self._set_title(self._read_plain)

    def push_carrier(self, carrier: encoders.RichTextPropertyEncoder) \
            -> encoders.RichTextPropertyEncoder:
        cannot_overwrite = (self.root.disable_overwrite and
                            not self.root.is_emptylike(self.reads()))
        if cannot_overwrite:
            return carrier
        ret = self.requestor.apply_prop(carrier)
        # this is always title
        self._set_title(carrier.plain_form())
        return ret
