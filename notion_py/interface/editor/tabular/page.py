from typing import Union, Optional

from notion_py.interface.common import PropertyFrame
from notion_py.interface.common.struct import AbstractRootEditor
from ..abs_supported.abs_child_bearing import ChildBearingBlock
from .pagelist_agents import PageListUpdater, PageListCreator


class TabularPageBlock(ChildBearingBlock):
    def __init__(self, caller: Union[AbstractRootEditor,
                                     PageListUpdater,
                                     PageListCreator],
                 page_id: str,
                 frame: Optional[PropertyFrame] = None):
        from .page_props import TabularProperty
        super().__init__(caller=caller, block_id=page_id)
        self.caller = caller
        if not frame:
            frame = caller.frame
        self.frame: PropertyFrame = frame
        self.props = TabularProperty(caller=self)
        self.agents.update(props=self.props)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    def preview(self):
        return {'tabular': self.props.preview(),
                'children': self.sphere.preview()}

    def execute(self):
        self.props.execute()
        if not self.archived:
            self.sphere.execute()

    def fully_read(self):
        return {'type': 'page',
                'tabular': self.props.read_of_all(),
                'children': self.sphere.reads()}

    def fully_read_rich(self):
        return {'type': 'page',
                'tabular': self.props.read_rich_of_all(),
                'children': self.sphere.reads_rich()}

    def set_overwrite_option(self, option: bool):
        self.props.set_overwrite_option(option)
