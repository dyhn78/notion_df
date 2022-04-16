from notion_zap.apps.prop_matcher.struct import MainEditorDepr, Processor
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter
from notion_zap.cli.editors import PageRow
from notion_zap.cli.structs import DatePropertyValue


class TimeFormatConformer(Processor):
    def __init__(self, bs: MainEditorDepr):
        super().__init__(bs)
        self.date_conformer = DateFormatConformer()
        self.week_conformer = WeekFormatConformer()

    def __call__(self):
        for date_row in self.bs.dates.rows:
            self.date_conformer(date_row)
        for week_row in self.bs.periods.rows:
            self.week_conformer(week_row)


class DateFormatConformer:
    def __init__(self, disable_overwrite=False):
        self.disable_overwrite = disable_overwrite

    def __call__(self, date_row: PageRow, date_title=None):
        """provide date_title manually if yet not synced to server-side"""
        if date_title is None:
            date_title = date_row.read_key_alias('title')
        date_handler = DateFormatter.from_date_title(date_title)
        date = date_handler.stringify_date()
        if date_title != date:
            date_row.write(key_alias='title', value=date)
        date_range = DatePropertyValue(date_handler.date)
        if date_range != date_row.read_key_alias('date_manual'):
            date_row.write_date(key_alias='date_manual', value=date_range)
        date_row.save()


class WeekFormatConformer:
    def __init__(self, disable_overwrite=False):
        self.disable_overwrite = disable_overwrite

    def __call__(self, week_row: PageRow, week_title=None):
        """provide period_title manually if yet-not-synced to server-side"""
        if week_title is None:
            week_title = week_row.read_key_alias('title')

        date_handler = DateFormatter.from_week_title(week_title)
        date_range = DatePropertyValue(start=date_handler.first_day_of_week(),
                                       end=date_handler.last_day_of_week())
        if date_range != week_row.read_key_alias('date_manual'):
            week_row.root.disable_overwrite = self.disable_overwrite
            week_row.write_date(key_alias='date_manual', value=date_range)
            week_row.root.disable_overwrite = False