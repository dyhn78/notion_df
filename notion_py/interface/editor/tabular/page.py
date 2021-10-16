from typing import Union, Optional

from notion_py.interface.common import PropertyFrame
from ..abs_supported.abs_child_bearing import ChildBearingBlock
from .pagelist_agents import PageListUpdater, PageListCreator
from ...common.struct import Editor


class TabularPageBlock(ChildBearingBlock):
    def __init__(self, caller: Union[Editor,
                                     PageListUpdater,
                                     PageListCreator],
                 page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller=caller, block_id=page_id)
        self.caller = caller
        if isinstance(caller, PageListCreator):
            self.yet_not_created = True
        if isinstance(caller, PageListCreator) or \
                isinstance(caller, PageListUpdater):
            frame = caller.frame
        self.frame = frame if frame else PropertyFrame()
        self.title = ''

        from .page_props import TabularPageProperty
        self.props = TabularPageProperty(caller=self)
        self.agents.update(props=self.props)

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
                'tabular': self.props.all_plain_keys(),
                'children': self.sphere.reads()}

    def fully_read_rich(self):
        return {'type': 'page',
                'tabular': self.props.all_rich_keys(),
                'children': self.sphere.reads_rich()}

    def set_overwrite_option(self, option: bool):
        self.props.set_overwrite_option(option)
