from __future__ import annotations

from typing import Union

from notion_zap.cli.gateway import encoders, parsers, requestors
from ..common.item import Item, ItemContents
from ..common.page import PageBlock, PagePayload
from ..structs.base_logic import RootGatherer
from ..common.with_items import ItemChildren


class PageItem(Item, PageBlock):
    def __init__(self, caller: Union[ItemChildren, RootGatherer], id_or_url: str):
        Item.__init__(self, caller, id_or_url)
        PageBlock.__init__(self, caller, id_or_url)

    def _initalize_payload(self, block_id: str):
        return PageItemContents(self, block_id)

    @property
    def contents(self) -> PageItemContents:
        # noinspection PyTypeChecker
        return self.payload


class PageItemContents(PagePayload, ItemContents,
                       encoders.PageContentsWriter):
    def __init__(self, caller: PageItem, block_id: str):
        PagePayload.__init__(self, caller, block_id)
        ItemContents.__init__(self, caller, block_id)
        self.caller = caller
        if self.block_id:
            requestor = requestors.UpdatePage(self)
        else:
            requestor = requestors.CreatePage(self, under_database=False)
        self._requestor = requestor
        assert self.regs['title']

    @property
    def requestor(self):
        return self._requestor

    def clear_requestor(self):
        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=False)

    def apply_page_parser(self, parser: parsers.PageParser):
        super().apply_page_parser(parser)
        self._read_plain = parser.values['title']
        self._read_rich = parser.rich_values['title']
        self._set_title(self._read_plain)

    def apply_block_parser(self, parser: parsers.BlockContentsParser):
        super().apply_block_parser(parser)
        self._set_title(self._read_plain)

    def push_encoder(self, carrier: encoders.RichTextPropertyEncoder) \
            -> encoders.RichTextPropertyEncoder:
        cannot_overwrite = (self.root.disable_overwrite and
                            not self.root.count_as_empty(self.read()))
        if cannot_overwrite:
            return carrier
        ret = self.requestor.apply_prop(carrier)
        # this is always title
        self._set_title(carrier.plain_form())
        return ret
