from __future__ import annotations
from typing import Union, Callable

from notion_zap.cli.gateway import encoders, parsers, requestors
from ..common.with_cc import ChildrenBearersContents
from ..common.with_contents import ContentsBearer
from ..common.with_items import ItemsBearer, ItemChildren
from .. import RootEditor


# TODO > Can-Have-Children 을 동적으로 바꿀 수 있을까?
class TextItem(ItemsBearer, ContentsBearer):
    def __init__(self,
                 caller: Union[ItemChildren,
                               RootEditor],
                 id_or_url: str):
        ItemsBearer.__init__(self, caller, id_or_url)
        ContentsBearer.__init__(self, caller, id_or_url)
        self.caller = caller

        self._contents = TextItemContents(self, id_or_url)

    def save_required(self) -> bool:
        return (self.contents.save_required() or
                self.items.save_required())

    def save_this(self):
        self.contents.save()
        if self.archived:
            return
        self.items.save()

    def save(self):
        if self.block_id:
            self.save_this()
        else:
            self.caller.save()

    @property
    def contents(self) -> TextItemContents:
        return self._contents

    @property
    def block_name(self):
        return self.contents.reads()

    def reads(self):
        return {'contents': self.contents.reads(),
                'children': self.items.reads(),
                'type': 'text'}

    def reads_rich(self):
        return {'contents': self.contents.reads_rich(),
                'children': self.items.reads_rich(),
                'type': 'text'}

    def save_info(self):
        return {'contents': self.contents.save_info(),
                **self.items.save_info(),
                'type': 'text'}


class TextItemContents(ChildrenBearersContents, encoders.TextContentsWriter):
    """
    when the master is called from TextItemsCreateAgent and thereby it is yet_not_created,
    they will insert blank paragraph as a default.
    """

    def __init__(self, caller: TextItem, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.caller = caller
        self._requestor = requestors.UpdateBlock(self)
        self._callback = None

    def push_carrier(self, carrier: encoders.RichTextContentsEncoder) \
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
            self.master.save()
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
