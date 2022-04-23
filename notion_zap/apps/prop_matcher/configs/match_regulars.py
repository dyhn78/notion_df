from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.struct import MatchOptions

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
