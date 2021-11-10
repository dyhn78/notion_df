from __future__ import annotations
from typing import Union, Callable

from notion_zap.interface.gateway import encoders, parsers, requestors
from ..common.with_cc import ChildrenBearersContents
from ..common.with_contents import ContentsBearer
from ..common.with_items import ItemsBearer, ItemAttachments
from ..root_editor import RootEditor


# TODO > Can-Have-Children 을 동적으로 바꿀 수 있을까?
class TextItem(ItemsBearer, ContentsBearer):
    def __init__(self,
                 caller: Union[ItemAttachments,
                               RootEditor],
                 block_id: str):
        ItemsBearer.__init__(self, caller)
        ContentsBearer.__init__(self, caller)
        self.caller = caller
        self._contents = TextItemContents(self, block_id)

        if isinstance(self.caller, ItemAttachments):
            self.caller.attach_text(self)

    def save_required(self) -> bool:
        return (self.contents.save_required() or
                self.attachments.save_required())

    def save_this(self):
        self.contents.save()
        if self.archived:
            return
        self.attachments.save()

    def save(self):
        if self.yet_not_created:
            self.caller.save()
        else:
            self.save_this()

    @property
    def contents(self) -> TextItemContents:
        return self._contents

    @property
    def block_name(self):
        return self.contents.reads()

    def reads(self):
        return {'contents': self.contents.reads(),
                'children': self.attachments.reads(),
                'type': 'text'}

    def reads_rich(self):
        return {'contents': self.contents.reads_rich(),
                'children': self.attachments.reads_rich(),
                'type': 'text'}

    def save_info(self):
        return {'contents': self.contents.save_info(),
                **self.attachments.save_info(),
                'type': 'text'}


class TextItemContents(ChildrenBearersContents, encoders.TextContentsWriter):
    """
    when the master is called from TextItemsCreateAgent and thereby it is yet_not_created,
    they will insert blank paragraph as a default.
    """

    def __init__(self, caller: TextItem, block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller
        self._requestor = requestors.UpdateBlock(self)
        self._callback = None

    def push_carrier(self, carrier: encoders.RichTextContentsEncoder) \
            -> encoders.RichTextContentsEncoder:
        self._can_have_children = carrier.can_have_children
        if self.yet_not_created:
            return self.callback(carrier)
        else:
            return self.requestor.apply_contents(carrier)

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

    def save(self):
        if self.yet_not_created:
            self.master.save()
        else:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update BlockContentsParser yourself without response
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
