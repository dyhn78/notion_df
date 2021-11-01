from typing import Union, Optional

from notion_py.interface.common import PropertyFrame
from ..common.pages import PageBlock
from ..common.struct import PointEditor
from ..root_editor import RootEditor


class PageRow(PageBlock):
    def __init__(self, caller: Union[RootEditor, PointEditor],
                 page_id: str,
                 yet_not_created=False,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(caller, page_id, yet_not_created)
        self.caller = caller
        self.frame = frame if frame else PropertyFrame()
        self.title = ''

        from .page_row_props import PageRowProperty
        self.props = PageRowProperty(caller=self)

    @classmethod
    def create_new(cls, caller):
        from .pagelist_agents import PageListCreator
        assert isinstance(caller, PageListCreator)
        self = cls(caller, '', True, caller.frame)
        return self

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
        # print('#######'
        #       f'{self.title}  '
        #       f'self.props: {self.props.has_updates()}  '
        #       f'self.attachments: {self.attachments.has_updates()}  ')
        self.props.save()
        if not self.archived:
            self.attachments.save()

    def reads(self):
        return {'type': 'page',
                'tabular': self.props.all_plain_keys(),
                'children': self.attachments.reads()}

    def reads_rich(self):
        return {'type': 'page',
                'tabular': self.props.all_rich_keys(),
                'children': self.attachments.reads_rich()}
