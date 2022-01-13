from __future__ import annotations
from typing import Union, Callable, Optional

from notion_zap.cli.gateway import parsers, requestors
from ..shared.document import Document
from ..shared.item import Item
from ..structs.base_logic import RootGatherer
from ..shared.with_items import BlockWithItems, ItemChildren
from ...gateway.encoders import (
    TextContentsWriter,
    RichTextContentsEncoder, ContentsEncoder,
)


class TextItem(Item, BlockWithItems, Document, TextContentsWriter):
    def __init__(self, caller: Union[ItemChildren, RootGatherer], id_or_url: str):
        self.callback: Optional[Callable[[RichTextContentsEncoder],
                                         RichTextContentsEncoder]] = None
        Item.__init__(self, caller, id_or_url)
        BlockWithItems.__init__(self, caller, id_or_url)
        self._requestor = requestors.UpdateBlock(self)

    @property
    def requestor(self) -> requestors.UpdateBlock:
        return self._requestor

    def clear_requestor(self):
        self._requestor = requestors.UpdateBlock(self)

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def push_encoder(self, encoder: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        self._can_have_children = encoder.can_have_children
        if self.block_id:
            return self.requestor.apply_contents(encoder)
        else:
            return self.callback(encoder)

    @property
    def block_name(self):
        return self.read_contents()

    def set_callback(
            self, value: Callable[[ContentsEncoder], ContentsEncoder]):
        self.callback = value

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
