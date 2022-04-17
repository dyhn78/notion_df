from __future__ import annotations

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.processors.bind_simple_props import BindSimpleProperties
from notion_zap.apps.prop_matcher.processors.conform_format import TimeFormatConformer
from notion_zap.apps.prop_matcher.processors.get_date_by_created_time \
    import DateProcessorByCreatedTime
from notion_zap.apps.prop_matcher.processors.get_date_by_earliest_ref \
    import DateProcessorByEarliestRef
from notion_zap.apps.prop_matcher.processors.get_week_by_date_ref \
    import PeriodProcessorByDateRef
from notion_zap.apps.prop_matcher.processors.get_week_by_from_date \
    import WeekRowProcessorFromDate
from notion_zap.apps.prop_matcher.processors.match_to_itself import SelfProcessor
from notion_zap.apps.prop_matcher.struct import MatchBase

REGULAR_MATCH_BASE = MatchBase({
    MyBlock.journals: {'itself', 'weeks', 'dates', 'dates_created'},
    MyBlock.counts: {'itself', 'weeks', 'dates', 'dates_created'},
    MyBlock.topics: {'itself', 'weeks', 'dates'},
    MyBlock.streams: {'itself', 'weeks', 'dates'},
    MyBlock.readings: {'itself', 'weeks_begin',
                       ('dates_begin', 'earliest_ref'), 'dates_created'},
    MyBlock.writings: {'itself', 'weeks', 'dates'},
    MyBlock.weeks: {'itself', 'date_manual'},
    MyBlock.dates: {'itself', 'date_manual', ('weeks', 'manual_date')},
})


class MatchController:
    def __init__(self, bs: MatchBase = None):
        if bs is None:
            bs = REGULAR_MATCH_BASE
        self.bs = bs
        self.root = bs.root
        self.fetch = MatchFetcher(self.bs)
        self.processor_groups = [
            [TimeFormatConformer(self.bs)],
            [DateProcessorByEarliestRef(self.bs)],  # created time보다 우선순위가 높아야 한다
            [DateProcessorByCreatedTime(self.bs),
             WeekRowProcessorFromDate(self.bs),
             PeriodProcessorByDateRef(self.bs),
             SelfProcessor(self.bs),
             BindSimpleProperties(self.bs)]
        ]

    def __call__(self, request_size=0):
        self.fetch(request_size)
        for group in self.processor_groups:
            for processor in group:
                processor()
            self.root.save()


# TODO : gcal_sync_status
class MatchFetcher:
    def __init__(self, bs: MatchBase):
        self.bs = bs
        self.root = self.bs.root

    def __call__(self, request_size=0):
        for key in self.bs.keys():
            self.fetch_table(key, request_size)

    def fetch_table(self, key: MyBlock, request_size: int):
        table = self.root.block_aliases[key]
        query = table.rows.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        block_option = self.bs.get_block_option(key)
        for tag in ['date_manual', 'itself', 'weeks', 'dates', 'dates_created']:
            if tag in block_option.keys():
                ft |= manager.relation(tag).is_empty()

        if key is MyBlock.readings:
            begin = manager.relation('periods_begin').is_empty()
            begin &= manager.checkbox('no_exp').is_empty()
            ft |= begin

            begin = manager.relation('dates_begin').is_empty()
            begin &= manager.checkbox('no_exp').is_empty()
            ft |= begin

            ft |= manager.select('media_type').is_empty()

        # ft.preview()
        query.push_filter(ft)
        query.execute(request_size)


if __name__ == '__main__':
    MatchController()(request_size=20)
