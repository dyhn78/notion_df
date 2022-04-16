from notion_zap.cli.editors import PageRow
from notion_zap.cli.structs import DateObject
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter


class PeriodIntroducer:
    def __init__(self, disable_overwrite=False):
        self.disable_overwrite = disable_overwrite

    def __call__(self, week: PageRow, week_title=None):
        """provide period_title manually if yet-not-synced to server-side"""
        if week_title is None:
            week_title = week.read_key_alias('title')

        date_handler = DateFormatter.from_week_title(week_title)
        date_range = DateObject(start=date_handler.first_day_of_week(),
                                end=date_handler.last_day_of_week())
        if date_range != week.read_key_alias('date_manual'):
            week.root.disable_overwrite = self.disable_overwrite
            week.write_date(key_alias='date_manual', value=date_range)
            week.root.disable_overwrite = False
