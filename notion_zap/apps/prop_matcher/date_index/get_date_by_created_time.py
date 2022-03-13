from __future__ import annotations

import datetime as dt
from typing import Union

from notion_zap.cli.editors import PageRow, Database
from notion_zap.cli.structs import DateObject
from notion_zap.apps.prop_matcher.common import has_value, set_value, query_unique_page_by_idx
from notion_zap.apps.prop_matcher.date_index.date_formatter import DateHandler
from notion_zap.apps.prop_matcher.struct import EditorBase, MainEditor


class DateMatcherByCreatedTime(MainEditor):
    def __init__(self, bs: EditorBase):
        super().__init__(bs)
        self.get_date = DateGetterFromDateValue(self.bs.dates)
        self.no_replace = True
        self.hour_offset = -5

    def __call__(self):
        for table, tag_date in self.args:
            for row in table.rows:
                if self.no_replace and has_value(row, tag_date):
                    continue
                date_val = self.get_date_val(row)
                if date := self.get_date(date_val):
                    set_value(row, date, tag_date)

    def get_date_val(self, row: PageRow):
        dom_idx: DateObject = row.read_tag('auto_datetime')
        date_val = dom_idx.start + dt.timedelta(hours=self.hour_offset)
        return date_val

    @property
    def args(self):
        args = []
        for table in [
            self.bs.journals,
            self.bs.checks,
            self.bs.topics,
            self.bs.writings,
            self.bs.tasks,
            self.bs.readings,
        ]:
            args.append((table, 'dates'))
        for table in [
            self.bs.journals,
            self.bs.checks,
            self.bs.readings,
        ]:
            args.append((table, 'dates_created'))
        return args


class DateGetterFromDateValue:
    def __init__(self, dates: Database):
        self.dates = dates
        self.dates_by_title = self.dates.rows.index_by_tag('title')

    def __call__(self, date_val: Union[dt.date, dt.datetime]):
        if tar := self.find_tar_by_date(date_val):
            return tar
        return self.create_tar_by_date(date_val)

    def find_tar_by_date(self, date_val: Union[dt.date, dt.datetime]):
        date_handler = DateHandler(date_val)
        tar_idx = date_handler.strf_dig6_and_weekday()
        if tar := self.dates_by_title.get(tar_idx):
            return tar
        if tar := query_unique_page_by_idx(self.dates, tar_idx, 'title', 'title'):
            return tar
        return None

    def create_tar_by_date(self, date_val: Union[dt.date, dt.datetime]):
        tar = self.dates.rows.open_new_page()
        date_handler = DateHandler(date_val)

        tar_idx = date_handler.strf_dig6_and_weekday()
        tar.write(key_alias='title', value=tar_idx)

        date_range = DateObject(date_handler.date)
        tar.write_date(key_alias='dateval_manual', value=date_range)
        return tar.save()
