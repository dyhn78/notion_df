from __future__ import annotations
from collections import defaultdict
from pprint import pprint
from typing import Optional

from .props import TabularProperty
from ..inline.supported import ChildBearingBlock
from ...api_format.parse import PageListParser
from ...struct import Editor, BridgeEditor, PropertyFrame


class PageList(Editor):
    def __init__(self, caller: Editor, callers_frame: PropertyFrame,
                 parent_id_if_yet_not_created=''):
        super().__init__(caller)
        self.caller = caller
        self.frame = callers_frame
        self._normal = NormalPageListContainer(self)
        self._new = NewPageListContainer(self)

        self._page_by_id = None
        self._id_by_title = None
        self._id_by_index = defaultdict(dict)
        self._ids_by_prop = defaultdict(dict)

    def __bool__(self):
        any([self._normal, self._new])

    def sync_master_id(self):
        self._new.sync_master_id()

    def preview(self):
        return {'pages': self._normal.preview(),
                'new_pages': self._new.preview()}

    def execute(self):
        self._normal.execute()
        response = self._new.execute()
        self._normal.values.extend(response)

    def page_by_id(self, page_id: str) -> TabularPageBlock:
        if self._page_by_id is None:
            self._page_by_id: dict[str, TabularPageBlock] \
                = {page.master_id: page for page in self._normal}
        return self._page_by_id[page_id]

    def id_by_title(self, page_title: str) -> str:
        if self._id_by_title is None:
            self._id_by_title = {page_object.title: page_object.master_id
                                 for page_object in self._normal}
        return self._id_by_title[page_title]

    def id_by_index(self, prop_name: str, index_value) -> str:
        if not self._id_by_index[prop_name]:
            try:
                res = {page_object.props.read_at(prop_name): page_object.master_id
                       for page_object in self._normal}
            except TypeError:
                page_object = self._normal[0]
                pprint(f"key : {page_object.props.read_at(prop_name)}")
                pprint(f"value : {page_object.master_id}")
                raise TypeError
            self._id_by_index[prop_name] = res
        return self._id_by_index[prop_name][index_value]

    def ids_by_prop(self, prop_name: str, prop_value) -> list[str]:
        if not self._ids_by_prop[prop_name]:
            res = defaultdict(list)
            for page_object in self._normal:
                res[page_object.props.read_at(prop_name)].append(page_object.master_id)
            self._ids_by_prop[prop_name] = res
        return self._ids_by_prop[prop_name][prop_value]


class NormalPageListContainer(BridgeEditor):
    def __init__(self, caller: PageList):
        super().__init__(caller)
        self.values: list[TabularPageBlock] = []
        self.frame = caller.frame

    def apply_parser(self, pagelist_parser: PageListParser):
        for page_parser in pagelist_parser:
            child_page = TabularPageBlock(page_parser.page_id, caller=self)
            child_page.props.apply_page_parser(page_parser)
            self.values.append(child_page)
        if pagelist_parser:
            self.frame.fetch_parser(pagelist_parser[0])


class NewPageListContainer(BridgeEditor):
    def __init__(self, caller: PageList, parent_id_if_yet_not_created=''):
        super().__init__(caller)
        self.caller = caller
        self._yet_not_created = bool(parent_id_if_yet_not_created)
        self.values: list[TabularPageBlock] = []

    def sync_master_id(self):
        if self._yet_not_created:
            for page in self.values:
                page.sync_parent_id()

    def new_tabular_page(self):
        page = TabularPageBlock.create_new(self)
        self.values.append(page)
        assert id(page) == id(self.values[-1])
        return page

    def execute(self):
        # individual tabular_page will update themselves.
        super().execute()
        res = self.values.copy()
        self.values.clear()
        return res


class TabularPageBlock(ChildBearingBlock):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[NormalPageListContainer] = None):
        super().__init__(page_id, caller=caller)
        self.frame = frame if frame else caller.frame
        database_id = self.parent_id if self.yet_not_created else ''
        self.props = TabularProperty(
            caller=self, callers_frame=self.frame,
            database_yet_not_created=not bool(self.parent_id),
            database_id_if_page_yet_not_created=database_id
        )
        self.agents.update(props=self.props)
        self.title = ''

    def sync_master_id(self):
        self.props.sync_master_id()
        self.children.sync_master_id()

    def sync_parent_id(self):
        self.props.sync_parent_id()

    def preview(self):
        return {'tabular': self.props.preview(),
                'children': self.children.preview()}

    def execute(self):
        """this is identical(except the first line) to InlinePageBlock.execute()"""
        self.props.execute()
        self.children.execute()

    def read(self):
        return {'type': 'page',
                'tabular': self.props.read_all_plain(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'type': 'page',
                'tabular': self.props.read_all_rich(),
                'children': self.children.reads_rich()}
