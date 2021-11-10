from typing import Union, Optional

from notion_zap.interface.common import PropertyFrame
from ..common.pages import PageBlock
from ..common.with_children import BlockChildren
from notion_zap.interface.editor.root_editor import RootEditor


class PageRow(PageBlock):
    def __init__(self, caller: Union[RootEditor, BlockChildren],
                 page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()

        from .page_row_props import PageRowProperty
        self.props = PageRowProperty(self, page_id)

        from .pagelist import PageList
        if isinstance(self.caller, PageList):
            self.caller.attach_page(self)

    @property
    def payload(self):
        return self.props

    @property
    def block_name(self):
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
