from __future__ import annotations

from typing import Union, Hashable

from notion_zap.cli.gateway import parsers, requestors
from ..shared.item import Item
from ..shared.page import PageBlock
from ..shared.with_items import ItemChildren
from ...core.base import RootSpace
from ...gateway.encoders import PageContentsWriter, RichTextPropertyEncoder


class PageItem(Item, PageBlock, PageContentsWriter):
    def __init__(self, caller: Union[ItemChildren, RootSpace], id_or_url: str,
                 alias: Hashable = None):
        Item.__init__(self, caller, id_or_url, alias)
        PageBlock.__init__(self, caller, id_or_url, alias)
        if self.block_id:
            requestor = requestors.UpdatePage(self)
        else:
            requestor = requestors.CreatePage(self, under_database=False)
        self._requestor = requestor

    @property
    def requestor(self):
        return self._requestor

    def clear_requestor(self):
        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=False)

    def _apply_page_parser(self, parser: parsers.PageParser):
        super()._apply_page_parser(parser)
        self._read_plain = parser.values['title']
        self._read_rich = parser.rich_values['title']
        self._title = self._read_plain

    def _apply_block_parser(self, parser: parsers.BlockParser):
        super()._apply_block_parser(parser)
        self._title = self._read_plain

    def push_encoder(self, carrier: RichTextPropertyEncoder) \
            -> RichTextPropertyEncoder:
        cannot_overwrite = (self.root.disable_overwrite and
                            self.root.eval_as_not_empty(self.read_contents()))
        if cannot_overwrite:
            return carrier
        ret = self.requestor.apply_prop(carrier)
        # this is always title
        # self._title = carrier.plain_form()
        return ret
