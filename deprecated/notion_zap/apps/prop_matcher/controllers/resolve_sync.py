from __future__ import annotations

from notion_zap.apps.myblock import MyBlock
from notion_zap.apps.prop_matcher.match_config import Frames
from notion_zap.apps.prop_matcher.utils.query_in_range import query_within_date_range
from notion_zap.cli.blocks import Database, PageRow
from notion_zap.cli.core.base import Root
from notion_zap.cli.utility import stopwatch


class SyncResolveController:
    tag__doms_date = 'auto_datetime'
    tag__doms_updom = 'up_self'
    tag__doms_downdom = 'down_self'

    def __init__(self, date_range=0):
        self.root = Root(print_response_heads=5)
        self.date_range = date_range
        self.marks = self.root.space.database(Frames[MyBlock.processes], )

    def execute(self):
        self.make_query()
        self.edit()
        self.root.save()

    def make_query(self):
        for domain in [self.marks]:
            query_within_date_range(domain, self.tag__doms_date, self.date_range)

    def edit(self):
        for domain in [self.marks]:
            algorithm = SyncResolver(
                domain, domain, self.tag__doms_downdom, self.tag__doms_updom)
            algorithm.execute()


class SyncResolver:
    def __init__(self, fronts: Database,
                 backs: Database,
                 tag_forward: str,
                 tag_backward: str):
        self.fronts = fronts
        self.backs = backs
        self.tag_forward = tag_forward
        self.tag_backward = tag_backward

    def execute(self):
        for front in self.fronts.rows:
            front_id = front.block_id
            back_ids = front.read_key_alias(self.tag_forward)
            for back_id in back_ids:
                back: PageRow = self.backs.rows.by_id[back_id]
                front_ids = back.read_key_alias(self.tag_backward)
                if front_id not in front_ids:
                    front_ids.append(front_id)
                    back.write_relation(key_alias=self.tag_backward, value=[front_id])
                    stopwatch(f"{back.block_name} -> {front.block_name}")
