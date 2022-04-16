from notion_zap.apps.prop_matcher.struct import EditorBase, MainEditor
from notion_zap.cli.editors import PageRow
from notion_zap.cli.structs import DatePropertyValue
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter


class TimeFormatConformer(MainEditor):
    def __init__(self, bs: EditorBase):
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

    def __call__(self, date: PageRow, date_title=None):
        """provide date_title manually if yet not synced to server-side"""
        if date_title is None:
            date_title = date.read_key_alias('title')
        date_handler = DateFormatter.from_strf_dig6(date_title)
        new_tar_idx = date_handler.stringify_date()
        if date_title != new_tar_idx:
            date.write(key_alias='title', value=new_tar_idx)
        date_range = DatePropertyValue(date_handler.date)
        if date_range != date.read_key_alias('date_manual'):
            date.write_date(key_alias='date_manual', value=date_range)
        date.save()


class WeekFormatConformer:
    def __init__(self, disable_overwrite=False):
        self.disable_overwrite = disable_overwrite

    def __call__(self, week: PageRow, week_title=None):
        """provide period_title manually if yet-not-synced to server-side"""
        if week_title is None:
            week_title = week.read_key_alias('title')

        date_handler = DateFormatter.from_week_title(week_title)
        date_range = DatePropertyValue(start=date_handler.first_day_of_week(),
                                       end=date_handler.last_day_of_week())
        if date_range != week.read_key_alias('date_manual'):
            week.root.disable_overwrite = self.disable_overwrite
            week.write_date(key_alias='date_manual', value=date_range)
            week.root.disable_overwrite = False