from __future__ import annotations

from notion_py.interface import RootEditor
from notion_py.interface.utility import stopwatch
from ..database_info import DatabaseInfo
from .frame import MatchFrames
from .common.query_maker import QueryMaker
from ...interface.editor.tabular import PageList, TabularPageBlock


class PropertySyncResolver:
    def __init__(self, date_range=0):
        self.root = RootEditor()
        self.date_range = date_range
        self.query_maker = QueryMaker(self.date_range)

        self.journals = self.root.open_pagelist(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS)

    def execute(self):
        self.make_query()
        self.edit()
        self.apply_results()

    def make_query(self):
        for pagelist in [self.journals]:
            self.query_maker.query_as_parents(pagelist, 'index_as_domain')

    def apply_results(self):
        for pagelist in [self.journals]:
            pagelist.execute()

    def edit(self):
        for pagelist in [self.journals]:
            algorithm = SyncResolveAlgorithm(pagelist, pagelist, 'down_self', 'up_self')
            algorithm.execute()


class SyncResolveAlgorithm:
    def __init__(self, fronts: PageList,
                 backs: PageList,
                 tag_forward: str,
                 tag_backward: str):
        self.fronts = fronts
        self.backs = backs
        self.tag_forward = tag_forward
        self.tag_backward = tag_backward

    def execute(self):
        for front in self.fronts:
            front_id = front.master_id
            back_ids = front.props.read_at(self.tag_forward)
            for back_id in back_ids:
                back: TabularPageBlock = self.backs.by_id[back_id]
                front_ids = back.props.read_at(self.tag_backward)
                if front_id not in front_ids:
                    front_ids.append(front_id)
                    back.props.write_at(self.tag_backward, front_id)
                    stopwatch(f"{back.master_name} -> {front.master_name}")
