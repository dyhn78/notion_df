import datetime as dt
from typing import Optional

from notion_zap.apps.prop_matcher.common.date_handler import DateHandler
from notion_zap.apps.prop_matcher.modules import DateMatcherAbs, PeriodMatcherAbs
from notion_zap.cli.editors import PageRow
from notion_zap.cli.structs import DateObject


class CalendarDateRange:
    def __init__(self, year_range: Optional[tuple[int, int]] = None):
        self.year_range = year_range
        if year_range:
            self.min_date = dt.date(year_range[0], 1, 1)
            self.max_date = dt.date(year_range[1], 1, 1)

    def iter_date(self):
        date_val = self.min_date
        while date_val < self.max_date:
            yield date_val
            date_val += dt.timedelta(days=1)


class DateTargetFiller(DateMatcherAbs):
    def __init__(self, bs, disable_overwrite: bool,
                 create_date_range: CalendarDateRange=None):
        super().__init__(bs)
        self.create_date_range = create_date_range
        self.disable_overwrite = disable_overwrite

    def execute(self):
        self.bs.root.disable_overwrite = self.disable_overwrite
        for tar in self.target.rows:
            self.update_tar(tar)
        if self.create_date_range:
            for date_val in self.create_date_range.iter_date():
                if self.find_tar_by_date(date_val):
                    continue
                self.create_tar_by_date(date_val)
        self.bs.root.disable_overwrite = False

    def update_tar(self, tar: PageRow, tar_idx=None):
        """provide tar_idx manually if yet not synced to server-side"""
        if tar_idx is None:
            tar_idx = tar.read_tag(self.Ttars_idx)
        date_handler = DateHandler.from_strf_dig6(tar_idx)
        new_tar_idx = date_handler.strf_dig6_and_weekday()
        if tar_idx != new_tar_idx:
            tar.write(tag=self.Ttars_idx, value=new_tar_idx)
        date_range = DateObject(date_handler.date)
        if date_range != tar.read_tag(self.Ttars_date):
            tar.write_date(tag=self.Ttars_date, value=date_range)
        tar.save()
        # print(f"{tar=}, {tar_idx=}, {date_range=},"
        #       f"{tar.props.read_at(self.Ttars_date)=},"
        #       f"{date_range != tar.props.read_at(self.Ttars_date)=}")


class PeriodTargetFiller(PeriodMatcherAbs):
    def __init__(self, bs, disable_overwrite,
                 create_date_range: CalendarDateRange = None):
        super().__init__(bs)
        self.disable_overwrite = disable_overwrite
        self.create_date_range = create_date_range

    def execute(self):
        for tar in self.target.rows:
            self.update_tar(tar, disable_overwrite=self.disable_overwrite)
        if self.create_date_range:
            for date_val in self.create_date_range.iter_date():
                if self.find_by_date_val(date_val):
                    continue
                self.create_by_date_val(date_val)