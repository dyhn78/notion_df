from typing import Union, Optional

from notion_py.interface.common import PropertyFrame
from ..common.pages import PageBlock
from ..common.struct import BlockEditor
from ..root_editor import RootEditor


class PageRow(PageBlock):
    def __init__(self, caller: Union[RootEditor, BlockEditor],
                 page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller, page_id)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()

        from .page_row_props import PageRowProperty
        self.props = PageRowProperty(caller=self)

    @property
    def payload(self):
        return self.props

    @property
    def master_name(self):
        return self.title

    def save_info(self):
        return {'tabular': self.props.save_info(),
                'children': self.attachments.save_info()}

    def save(self):
        self.props.save()
        if self.archived:
            return
        self.attachments.save()

    def reads(self):
        return {'type': 'page',
                'tabular': self.props.all_plain_keys(),
                'children': self.attachments.reads()}

    def reads_rich(self):
        return {'type': 'page',
                'tabular': self.props.all_rich_keys(),
                'children': self.attachments.reads_rich()}
