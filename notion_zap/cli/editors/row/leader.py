from typing import Union, Optional

from notion_zap.cli.structs import PropertyFrame
from ..common.page import PageBlock
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

        from .props import PageRowProperties
        self.props = PageRowProperties(self, id_or_url)

    @property
    def payload(self):
        return self.props

    def save(self):
        self.props.save()
        if not self.archived:
            self.items.save()
        return self
