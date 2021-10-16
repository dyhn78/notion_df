from typing import Union, Optional

from notion_py.interface.encoder import TextContentsWriter, RichTextContentsEncoder
from notion_py.interface.parser import BlockContentsParser
from notion_py.interface.requestor import UpdateBlock, RetrieveBlock
from ..abs_supported.abs_child_bearing.abs_contents_bearing.contents_bearing import \
    ContentsBearingBlock, BlockContents
from ..abs_supported.abs_child_bearing.creator import \
    TextBlocksCreator
from ..abs_supported.abs_child_bearing.updater import BlockSphereUpdater
from ...common.struct import Editor


class TextBlock(ContentsBearingBlock):
    def __init__(self,
                 caller: Union[Editor,
                               BlockSphereUpdater,
                               TextBlocksCreator],
                 block_id: str):
        super().__init__(caller=caller, block_id=block_id)
        self.caller = caller
        if isinstance(caller, TextBlocksCreator):
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
    def __init__(self, caller: TextBlock,
                 creator: Optional[TextBlocksCreator] = None):
        super().__init__(caller)
        self.caller = caller
        self.creator = creator
        self._requestor = UpdateBlock(self)

    @property
    def gateway(self) -> UpdateBlock:
        return self._requestor

    @gateway.setter
    def gateway(self, value):
        self._requestor = value

    def archive(self):
        self.gateway.archive()

    def un_archive(self):
        self.gateway.un_archive()

    def retrieve(self):
        requestor = RetrieveBlock(self)
        response = requestor.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        if self.yet_not_created:
            self.master.execute()
        else:
            self.gateway.execute()
            # TODO: update {self._read};
            #  1. use the <response> = self.gateway.execute()
            #  2. update BlockContentsParser yourself without response
        self.gateway = UpdateBlock(self)

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        # print(f"<{self.master_id}>")
        # print(f"<{self.parent_id}>")
        # print(self.yet_not_created)
        # print(self.master.yet_not_created)
        # print(self.master.caller.yet_not_created)
        # print(self.parent.yet_not_created)
        # print(carrier.unpack())
        if self.yet_not_created:
            return self.creator.push_carrier(self, carrier)
        else:
            return self.gateway.apply_contents(carrier)
