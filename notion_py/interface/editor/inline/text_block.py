from typing import Union, Optional

from notion_py.interface.editor.abs_supported.abs_child_bearing.abs_contents_bearing.master import \
    ContentsBearingBlock, BlockContents
from ..abs_supported.abs_child_bearing.creater_page_as_indep import \
    BlockSphereCreatorWithIndepInlinePage
from ..abs_supported.abs_child_bearing.creater_page_as_child import \
    BlockSphereCreatorWithChildInlinePage
from notion_py.interface.struct import PointEditor, Editor, GroundEditor
from ...api_encode import TextContentsWriter, RichTextContentsEncoder
from ...api_parse import BlockContentsParser
from ...gateway import UpdateBlock, RetrieveBlock


class TextBlock(ContentsBearingBlock):
    def __init__(self, caller: Union[Editor, PointEditor], block_id: str):
        super().__init__(caller=caller, block_id=block_id)
        if isinstance(caller, BlockSphereCreatorWithChildInlinePage) or \
                isinstance(caller, BlockSphereCreatorWithIndepInlinePage):
            self.contents = TextContents(self, caller)
        else:
            self.contents = TextContents(self)
        self.agents.update(contents=self.contents)

    @property
    def master_name(self):
        return self.contents.read

    def execute(self):
        if self.yet_not_created:
            self.caller.execute()
        else:
            self.contents.execute()
            self.sphere.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='text')

    def fully_read_rich(self):
        return dict(**super().fully_read_rich(), type='text')


class TextContents(BlockContents, TextContentsWriter):
    def __init__(self, caller: PointEditor, uncle: Optional[GroundEditor] = None):
        super().__init__(caller)
        self.caller = caller
        if self.yet_not_created:
            self.gateway = uncle.gateway
        else:
            self.gateway = UpdateBlock(self)

    def retrieve(self):
        gateway = RetrieveBlock(self)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self.yet_not_created:
            self.gateway = UpdateBlock(self)
        return response
        # TODO: update {self._read};
        #  consider making BlockContentsParser yourself without response

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)