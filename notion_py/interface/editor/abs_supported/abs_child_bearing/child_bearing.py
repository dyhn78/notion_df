from __future__ import annotations
from abc import abstractmethod
from typing import Union

from notion_py.interface.common.struct import Editor

from ..supported import SupportedBlock
from ...struct import PointEditor


class ChildBearingBlock(SupportedBlock):
    @abstractmethod
    def __init__(self, caller: Union[PointEditor, Editor], block_id: str):
        super().__init__(caller, block_id)
        self.caller = caller
        self.is_supported_type = True
        self.can_have_children = True
        self.has_children = False

        from .sphere import BlockSphere
        self.sphere = BlockSphere(self)
        self.agents.update(children=self.sphere)

    @abstractmethod
    def preview(self):
        return {'contents': "unpack contents here",
                'children': "unpack children here"}

    @abstractmethod
    def execute(self):
        """
        1. since self.sphere go first than self.new_children,
            assigning a multi-indented structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.tabular,
            have to refer to self.master_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """
        return
