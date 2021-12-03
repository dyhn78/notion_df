from __future__ import annotations
from typing import Union, Callable

from notion_zap.cli.gateway import encoders, parsers, requestors
from ..common.document import Document
from ..common.item import Item, ItemContents
from ..structs.base_logic import RootRegistry
from ..common.with_items import BlockWithItems, ItemChildren


class TextItem(Item, BlockWithItems, Document):
    def __init__(self, caller: Union[ItemChildren, RootRegistry], id_or_url: str):
        Item.__init__(self, caller, id_or_url)
        BlockWithItems.__init__(self, caller, id_or_url)

    def _initalize_payload(self, block_id):
        return TextItemContents(self, block_id)

    @property
    def contents(self) -> TextItemContents:
        # noinspection PyTypeChecker
        return self.payload

    @property
    def block_name(self):
        return self.contents.read()

    def save(self):
        if self.block_id:
            self.save_this()
        else:
            self.caller.save()

    def save_this(self):
        self.contents.save()
        if self.archived:
            return
        self.items.save()


class TextItemContents(ItemContents, encoders.TextContentsWriter):
    """
    when the block is called from TextItemsCreateAgent and thereby it is yet_not_created,
    they will insert blank paragraph as a default.
    """

    def __init__(self, caller: TextItem, block_id):
        super().__init__(caller, block_id)
        self.caller = caller
        self._requestor = requestors.UpdateBlock(self)
        self._callback = None

    def push_encoder(self, carrier: encoders.RichTextContentsEncoder) \
            -> encoders.RichTextContentsEncoder:
        self._can_have_children = carrier.can_have_children
        if self.block_id:
            return self.requestor.apply_contents(carrier)
        else:
            return self.callback(carrier)

    @property
    def callback(self) -> Callable[[encoders.RichTextContentsEncoder],
                                   encoders.RichTextContentsEncoder]:
        return self._callback

    def set_callback(
            self, value: Callable[[encoders.ContentsEncoder], encoders.ContentsEncoder]):
        self._callback = value

    def set_placeholder(self):
        self.write_paragraph('')

    def retrieve(self):
        requestor = requestors.RetrieveBlock(self)
        response = requestor.execute()
        parser = parsers.BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)
        requestor.print_comments()

    def save(self):
        if self.block_id:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update BlockContentsParser yourself without response
        else:
            self.block.save()
        self.clear_requestor()

    @property
    def requestor(self) -> requestors.UpdateBlock:
        return self._requestor

    def clear_requestor(self):
        self._requestor = requestors.UpdateBlock(self)

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()
