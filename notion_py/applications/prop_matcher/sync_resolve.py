from __future__ import annotations

from notion_py.interface import editor
from ...interface.common import utility
from .common.frame import MatchFrames
from .common.query_maker import query_within_date_range
from ..database_info import DatabaseInfo


class PropertySyncResolver:
    def __init__(self, date_range=0):
        self.root = editor.RootEditor()
        self.date_range = date_range
        self.journals = self.root.open_database(*DatabaseInfo.JOURNALS,
                                                frame=MatchFrames.JOURNALS).pagelist

    def execute(self):
        self.make_query()
        self.edit()
        self.root.save()

    def make_query(self):
        for pagelist in [self.journals]:
            query_within_date_range(pagelist, 'index_as_domain', self.date_range)

    def edit(self):
        for pagelist in [self.journals]:
            algorithm = SyncResolveAlgorithm(pagelist, pagelist, 'down_self', 'up_self')
            algorithm.execute()


class SyncResolveAlgorithm:
    def __init__(self, fronts: editor.PageList,
                 backs: editor.PageList,
                 tag_forward: str,
                 tag_backward: str):
        self.fronts = fronts
        self.backs = backs
        self.tag_forward = tag_forward
        self.tag_backward = tag_backward

    def execute(self):
        for front in self.fronts:
            front_id = front.block_id
            back_ids = front.props.read_at(self.tag_forward)
            for back_id in back_ids:
                back: editor.PageRow = self.backs.by_id[back_id]
                front_ids = back.props.read_at(self.tag_backward)
                if front_id not in front_ids:
                    front_ids.append(front_id)
                    back.props.write_at(self.tag_backward, front_id)
                    utility.stopwatch(f"{back.block_name} -> {front.block_name}")
