from __future__ import annotations
from typing import Union, Callable

from notion_zap.cli.gateway import parsers, requestors
from ..shared.document import Document
from ..shared.item import Item
from ..structs.base_logic import RootGatherer
from ..shared.with_items import BlockWithItems, ItemChildren
from ...gateway.encoders import (
    TextContentsWriter,
    RichTextContentsEncoder,
    ContentsEncoder
)


class TextItem(Item, BlockWithItems, Document, TextContentsWriter):
    def __init__(self, caller: Union[ItemChildren, RootGatherer], id_or_url: str):
        BlockWithItems.__init__(self, caller, id_or_url)
        Item.__init__(self, caller, id_or_url)
        self._requestor = requestors.UpdateBlock(self)
        self._callback = None
        self._can_have_children = None

    @property
    def requestor(self) -> requestors.UpdateBlock:
        return self._requestor

    def clear_requestor(self):
        self._requestor = requestors.UpdateBlock(self)

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def push_encoder(self, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        self._can_have_children = carrier.can_have_children
        if self.block_id:
            return self.requestor.apply_contents(carrier)
        else:
            return self.callback(carrier)

    @property
    def block_name(self):
        return self.read_contents()

    @property
    def callback(self) -> Callable[[RichTextContentsEncoder],
                                   RichTextContentsEncoder]:
        return self._callback

    def set_callback(
            self, value: Callable[[ContentsEncoder], ContentsEncoder]):
        self._callback = value

    def set_placeholder(self):
        self.write_paragraph('')

    def retrieve(self):
        requestor = requestors.RetrieveBlock(self)
        response = requestor.execute()
        parser = parsers.BlockParser.parse_retrieve(response)
        self.apply_block_parser(parser)
        requestor.print_comments()

    def _save_this(self):
        if self.block_id:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update BlockParser yourself without response
        else:
            self.caller.save()
        self.clear_requestor()
        return self
