from __future__ import annotations

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.processors.bind_simple_props import BindSimpleProperties
from notion_zap.apps.prop_matcher.processors.conform_format import TimeFormatConformer
from notion_zap.apps.prop_matcher.processors.get_date_from_created_time \
    import DateProcessorByCreatedTime
from notion_zap.apps.prop_matcher.processors.get_date_from_refs_earliest \
    import DateProcessorByEarliestRef
from notion_zap.apps.prop_matcher.processors.get_week_from_manual_date \
    import WeekProcessorFromManualDate
from notion_zap.apps.prop_matcher.processors.get_week_from_ref_date \
    import WeekProcessorFromRefDate
from notion_zap.apps.prop_matcher.processors.match_to_itself import SelfProcessor
from notion_zap.apps.prop_matcher.struct import MatchOptions, init_root, Saver
from notion_zap.cli.editors import Root
from notion_zap.cli.editors.database.main import QueryWithCallback
from notion_zap.cli.gateway.requestors.query.filter_struct import QueryFilter

REGULAR_MATCH_OPTIONS = MatchOptions({
    MyBlock.journals: {'itself', 'weeks', 'dates', 'dates_created'},
    MyBlock.counts: {'itself', 'weeks', 'dates', 'dates_created'},
    MyBlock.issues: {'itself', 'weeks', 'dates'},
    MyBlock.streams: {'itself', 'weeks', 'dates'},
    MyBlock.readings: {'itself', 'weeks_begin',
                       ('dates_begin', 'ignore_book_with_no_exp'), 'dates_created'},
    MyBlock.writings: {'itself', 'weeks', 'dates'},
    MyBlock.weeks: {'itself', 'manual_date'},
    MyBlock.dates: {'itself', 'manual_date', ('weeks', 'manual_date')},
})


class MatchController:
    def __init__(self, option: MatchOptions = None):
        if option is None:
            self.option = REGULAR_MATCH_OPTIONS
        self.root = init_root()
        self.fetch = MatchFetcher(self.root, self.option)
        self.processes = [
            TimeFormatConformer(self.root, self.option),
            Saver(self.root),

            DateProcessorByEarliestRef(self.root, self.option),
            Saver(self.root),

            DateProcessorByCreatedTime(self.root, self.option),
            WeekProcessorFromManualDate(self.root, self.option),
            WeekProcessorFromRefDate(self.root, self.option),
            SelfProcessor(self.root, self.option),
            BindSimpleProperties(self.root, self.option),
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
        for block_key in self.option:
            query, ft = self.get_query_filter(block_key)
            query.push_filter(ft)
            query.execute(request_size)
            ft.preview()
            print('')

    # TODO : gcal_sync_status
    def get_query_filter(self, block_key: MyBlock) -> tuple[QueryWithCallback, QueryFilter]:
        table = self.root.block_aliases[block_key]
        query = table.rows.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        for option_key in ['itself', 'weeks', 'dates', 'dates_created']:
            if block_key in self.option.filter_key(option_key):
                ft |= manager.relation(option_key).is_empty()
        for option_key in ['manual_date']:
            if block_key in self.option.filter_key(option_key):
                ft |= manager.date(option_key).is_empty()

        if block_key is MyBlock.readings:
            begin = manager.relation('weeks_begin').is_empty()
            begin &= manager.checkbox('no_exp_book').is_empty()
            ft |= begin

            begin = manager.relation('dates_begin').is_empty()
            begin &= manager.checkbox('no_exp_book').is_empty()
            ft |= begin

            media_type = manager.relation('channels').is_not_empty()
            media_type &= manager.select('media_type').is_empty()
            ft |= media_type

        return query, ft


if __name__ == '__main__':
    controller = MatchController()
    controller(request_size=5)
