from __future__ import annotations

from notion_zap.apps.myblock import MyBlock
from notion_zap.apps.prop_matcher.match_struct import MatchOptions, init_root, Saver
from notion_zap.apps.prop_matcher.processors.date_by_created_time \
    import DateProcessorByCreatedTime
from notion_zap.apps.prop_matcher.processors.date_by_ref_earliest \
    import DateProcessorByRefEarliest
from notion_zap.apps.prop_matcher.processors.property_by_ref import PropertyProcessorByReference
from notion_zap.apps.prop_matcher.processors.time_format_conformer import TimeFormatConformer
from notion_zap.apps.prop_matcher.processors.week_by_manual_date \
    import WeekProcessorByManualDate
from notion_zap.apps.prop_matcher.processors.week_by_ref_date \
    import WeekProcessorFromRefDate
from notion_zap.cli.blocks.database.database import QueryWithCallback, Database
from notion_zap.cli.core.base import Root
from notion_zap.cli.gateway.requestors.query.filter_struct import QueryFilter

REGULAR_MATCH_OPTIONS = MatchOptions({
    MyBlock.weeks: {'manual_date'},
    MyBlock.dates: {'manual_date', ('weeks', 'manual_date')},

    MyBlock.processes: {'weeks', 'dates', 'dates_created'},
    MyBlock.events: {'weeks', 'dates', 'dates_created'},

    MyBlock.journals: {'weeks', 'dates'},
    MyBlock.issues: {'weeks', 'dates'},
    MyBlock.tasks: {'weeks', 'dates'},

    MyBlock.readings: {('weeks', "warning: but don't make filter"),
                       ('dates', "warning: but don't make filter"),
                       'weeks_begin', 'dates_begin', 'dates_created'},
    MyBlock.points: {'weeks', 'dates'},
})


class MatchController:
    def __init__(self, option: MatchOptions = None):
        if option is None:
            self.option = REGULAR_MATCH_OPTIONS
        self.root = init_root()
        self.fetch = MatchFetcher(self.root, self.option)
        self.processes = [
            TimeFormatConformer(self.root, self.option),
            DateProcessorByRefEarliest(self.root, self.option),
            DateProcessorByCreatedTime(self.root, self.option),
            WeekProcessorFromRefDate(self.root, self.option),
            WeekProcessorByManualDate(self.root, self.option),
            PropertyProcessorByReference(self.root, self.option),
            Saver(self.root),
        ]

    def __call__(self, request_size=0):
        self.fetch(request_size)
        for process in self.processes:
            process()


class MatchFetcher:
    def __init__(self, root: Root, option: MatchOptions):
        self.root = root
        self.option = option

    def __call__(self, request_size=0):
        block_keys = (block for block in MyBlock if block in self.option)
        for block_key in block_keys:
            query, ft = self.get_query_filter(block_key)
            query.push_filter(ft)
            query.execute(request_size)
            ft.preview()
            print('')

    def get_query_filter(self, block_key: MyBlock) -> tuple[QueryWithCallback, QueryFilter]:
        table: Database = self.root[block_key]
        query = table.rows.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        for option_key in ['weeks', 'dates', 'dates_created']:
            if block_key in self.option.filter_pair(option_key):
                ft |= manager.relation(option_key).is_empty()
        for option_key in ['manual_date']:
            if block_key in self.option.filter_key(option_key):
                ft |= manager.date(option_key).is_empty()

        if block_key is MyBlock.readings:
            weeks_begin = manager.relation('weeks_begin').is_empty()
            weeks_begin &= manager.relation('dates_begin').is_not_empty()
            ft |= weeks_begin

            dates_begin_by_earliest_ref = manager.relation('dates_begin').is_empty()
            dates_begin_by_earliest_ref &= manager.relation('processes').is_not_empty()
            ft |= dates_begin_by_earliest_ref

            dates_begin_from_created_time = manager.relation('dates_begin').is_empty()
            dates_begin_from_created_time &= manager.checkbox(
                'get_dates_begin_from_created_time').is_not_empty()
            ft |= dates_begin_from_created_time

            media_type_from_streams = manager.select('media_type').is_empty()
            media_type_from_streams &= manager.relation('streams').is_not_empty()
            ft |= media_type_from_streams

        return query, ft


if __name__ == '__main__':
    controller = MatchController()
    controller(request_size=5)
