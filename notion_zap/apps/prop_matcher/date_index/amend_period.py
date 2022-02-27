from notion_zap.cli.editors import PageRow
from notion_zap.cli.structs import DateObject
from notion_zap.apps.prop_matcher.date_index.date_formatter import DateHandler


class PeriodIntroducer:
    def __init__(self, disable_overwrite=False):
        self.disable_overwrite = disable_overwrite

    def __call__(self, period: PageRow, period_title=None):
        """provide period_title manually if yet-not-synced to server-side"""
        if period_title is None:
            period_title = period.read_tag('title')

        date_handler = DateHandler.from_strf_year_and_week(period_title)
        date_range = DateObject(start=date_handler.first_day_of_week(),
                                end=date_handler.last_day_of_week())
        if date_range != period.read_tag('manual_date_range'):
            period.root.disable_overwrite = self.disable_overwrite
            period.write_date(tag='manual_date_range', value=date_range)
            period.root.disable_overwrite = False
