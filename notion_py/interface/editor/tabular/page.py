from typing import Union, Optional

from ..abs_supported.abs_child_bearing.master import ChildBearingBlock
from notion_py.interface.editor.tabular.page_props import TabularProperty
from notion_py.interface.struct import Editor, BridgeEditor, PropertyFrame


class TabularPageBlock(ChildBearingBlock):
    def __init__(self, caller: Union[Editor, BridgeEditor],
                 page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller=caller, block_id=page_id)
        if not frame:
            frame = getattr(caller, 'frame', PropertyFrame())
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
