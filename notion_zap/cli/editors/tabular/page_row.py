from typing import Union, Optional

from notion_zap.cli.struct import PropertyFrame
from ..common.pages import PageBlock
from ..common.with_children import BlockChildren
from notion_zap.cli.editors.root_editor import RootEditor


class PageRow(PageBlock):
    def __init__(self, caller: Union[RootEditor, BlockChildren],
                 id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()

        from .page_row_props import PageRowProperties
        self.props = PageRowProperties(self, id_or_url)

        from .pagelist import PageList
        if isinstance(self.caller, PageList):
            self.caller.attach(self)

    @property
    def payload(self):
        return self.props

    @property
    def block_name(self):
        return self.title

    def save_info(self):
        return {'tabular': self.props.save_info(),
                'children': self.items.save_info()}

    def save(self):
        self.props.save()
        if not self.archived:
            self.items.save()
        return self

    def reads(self):
        return {'type': 'page',
                'tabular': self.props.all_plain_keys(),
                'children': self.items.reads()}

    def reads_rich(self):
        return {'type': 'page',
                'tabular': self.props.all_rich_keys(),
                'children': self.items.reads_rich()}
