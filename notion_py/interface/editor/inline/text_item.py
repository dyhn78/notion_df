from __future__ import annotations
from typing import Union

from notion_py.interface.encoder import (
    TextContentsWriter, RichTextContentsEncoder)
from notion_py.interface.parser import BlockContentsParser
from notion_py.interface.requestor import UpdateBlock, RetrieveBlock
from ..common.with_contents import (
    ContentsBearer, BlockContents)
from ..common.with_items import (
    ItemsBearer, ItemsUpdater, TextItemsCreateAgent)
from ..root_editor import RootEditor


# TODO > Can-Have-Children 을 동적으로 바꿀 수 있을까?
class TextItem(ContentsBearer, ItemsBearer):
    def __init__(self,
                 caller: Union[TextItemsCreateAgent,
                               ItemsUpdater,
                               RootEditor],
                 block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller
        self.contents = TextContents(self)

    @property
    def contents(self) -> TextContents:
        return self._contents

    @contents.setter
    def contents(self, value: TextContents):
        self._contents = value

    def save_required(self) -> bool:
        return (self.contents.save_required() or
                self.attachments.save_required())

    @classmethod
    def create_new(cls, caller: TextItemsCreateAgent):
        self = cls(caller, '')
        return self

    @property
    def master_name(self):
        return self.contents.reads()

    def save(self):
        if self.yet_not_created:
            self.caller.save()
        else:
            self.save_this()

    def save_this(self):
        self.contents.save()
        if self.archived:
            return
        self.attachments.save()

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

    def push_contents_carrier(self, carrier):
        return self.caller.push_carrier(self, carrier)


class TextContents(BlockContents, TextContentsWriter):
    def __init__(self, caller: TextItem):
        super().__init__(caller)
        self.caller = caller
        self._requestor = UpdateBlock(self)

    @property
    def requestor(self) -> UpdateBlock:
        return self._requestor

    @requestor.setter
    def requestor(self, value):
        self._requestor = value

    def archive(self):
        self.requestor.archive()

    def un_archive(self):
        self.requestor.un_archive()

    def retrieve(self):
        requestor = RetrieveBlock(self)
        response = requestor.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def save(self):
        if self.yet_not_created:
            self.master.save()
        else:
            self.requestor.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update BlockContentsParser yourself without response
        self.requestor = UpdateBlock(self)

    def push_carrier(self, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        if self.yet_not_created:
            return self.caller.push_contents_carrier(carrier)
        else:
            return self.requestor.apply_contents(carrier)
