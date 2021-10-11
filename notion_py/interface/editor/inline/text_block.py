from typing import Union, Optional

from ..abs_supported.abs_child_bearing.abs_contents_bearing.master import \
    ContentsBearingBlock, BlockContents
from ..abs_supported.abs_child_bearing.creator import \
    BlockSphereCreator
from ..abs_supported.abs_child_bearing.updater import BlockSphereUpdater
from notion_py.interface.encoder import TextContentsWriter, RichTextContentsEncoder
from notion_py.interface.parser import BlockContentsParser
from notion_py.interface.requestor import UpdateBlock, RetrieveBlock
from ...common.struct import AbstractRootEditor


class TextBlock(ContentsBearingBlock):
    def __init__(self,
                 caller: Union[AbstractRootEditor,
                               BlockSphereUpdater,
                               BlockSphereCreator],
                 block_id: str):
        super().__init__(caller=caller, block_id=block_id)
        self.caller = caller
        if isinstance(caller, BlockSphereCreator):
            self.yet_not_created = True
            self.contents = TextContents(self, caller)
        else:
            self.contents = TextContents(self)
        self.agents.update(contents=self.contents)

    @property
    def master_name(self):
        return self.contents.read()

    def execute(self):
        if self.yet_not_created:
            self.caller.execute()
            self.yet_not_created = False
        else:
            self.contents.execute()
            if self.archived:
                return
            self.sphere.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='text')

    def fully_read_rich(self):
        return dict(**super().fully_read_rich(), type='text')


class TextContents(BlockContents, TextContentsWriter):
    def __init__(self, caller: TextBlock, uncle: Optional[BlockSphereCreator] = None):
        super().__init__(caller)
        self.caller = caller
        if self.yet_not_created:
            self._gateway_before_created = uncle.gateway
        self._gateway_after_created = UpdateBlock(self)

    @property
    def gateway(self):
        if self.yet_not_created:
            return self._gateway_before_created
        else:
            return self._gateway_after_created

    @gateway.setter
    def gateway(self, value):
        self._gateway_after_created = value

    def retrieve(self):
        gateway = RetrieveBlock(self)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        if self.yet_not_created:
            self.master.execute()
        else:
            response = self.gateway.execute()
            # TODO: update {self._read};
            #  consider making BlockContentsParser yourself without response
            self.gateway = UpdateBlock(self)
            return response

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        # print(f"<{self.master_id}>")
        # print(f"<{self.parent_id}>")
        # print(self.yet_not_created)
        # print(self.master.yet_not_created)
        # print(self.master.caller.yet_not_created)
        # print(self.parent.yet_not_created)
        # print(carrier.unpack())
        return self.gateway.apply_contents(carrier)
