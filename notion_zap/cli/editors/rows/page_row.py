from typing import Union, Optional

from notion_zap.cli.struct import PropertyFrame
from ..common.pages import PageBlock
from ..common.with_children import BlockChildren
from ..structs.leaders import Root


class PageRow(PageBlock):
    def __init__(self, caller: Union[Root, BlockChildren],
                 id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        from ..database.leaders import RowChildren
        assert isinstance(caller, Root) or isinstance(caller, RowChildren)

        super().__init__(caller, id_or_url)
        self.caller = caller

        self.frame = frame if frame else PropertyFrame()

        from .page_row_props import PageRowProperties
        self.props = PageRowProperties(self, id_or_url)

    @property
    def payload(self):
        return self.props

    @property
    def block_name(self):
        return self.title

    def save_info(self):
        return {'type': 'page',
                'id': self.block_id,
                'props': self.props.save_info(),
                'children': self.items.save_info()}

    def save(self):
        self.props.save()
        if not self.archived:
            self.items.save()
        return self

    def read(self):
        return {'type': 'page',
                'id': self.block_id,
                'props': self.props.all_plain_keys(),
                'children': self.items.read()}

    def richly_read(self):
        return {'type': 'page',
                'id': self.block_id,
                'props': self.props.all_rich_keys(),
                'children': self.items.richly_read()}
