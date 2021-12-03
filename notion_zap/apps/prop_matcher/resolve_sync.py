from __future__ import annotations

from notion_zap.cli import editors
from notion_zap.cli.utility import stopwatch
from notion_zap.apps.config.common import DatabaseInfo
from notion_zap.apps.config.prop_matcher import MatchFrames
from .common.query_maker import query_within_date_range


class SyncResolveController:
    tag__doms_date = 'auto_datetime'
    tag__doms_updom = 'up_self'
    tag__doms_downdom = 'down_self'

    def __init__(self, date_range=0):
        self.root = editors.Root()
        self.date_range = date_range
        self.journals = self.root.objects.database(*DatabaseInfo.JOURNALS,
                                                    MatchFrames.JOURNALS)

    def execute(self):
        self.make_query()
        self.edit()
        self.root.save()

    def make_query(self):
        for domain in [self.journals]:
            query_within_date_range(domain, self.tag__doms_date, self.date_range)

    def edit(self):
        for domain in [self.journals]:
            algorithm = SyncResolver(
                domain, domain, self.tag__doms_downdom, self.tag__doms_updom)
            algorithm.execute()


class SyncResolver:
    def __init__(self, fronts: editors.Database,
                 backs: editors.Database,
                 tag_forward: str,
                 tag_backward: str):
        self.fronts = fronts
        self.backs = backs
        self.tag_forward = tag_forward
        self.tag_backward = tag_backward

    def execute(self):
        for front in self.fronts.rows:
            front_id = front.block_id
            back_ids = front.props.read_tag(self.tag_forward)
            for back_id in back_ids:
                back: editors.PageRow = self.backs.rows.by_id[back_id]
                front_ids = back.props.read_tag(self.tag_backward)
                if front_id not in front_ids:
                    front_ids.append(front_id)
                    back.props.write_relation(tag=self.tag_backward, value=front_id)
                    stopwatch(f"{back.block_name} -> {front.block_name}")