from __future__ import annotations

import datetime as dt
from typing import Union

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.common import (
    has_relation, set_relation, query_unique_page_by_idx)
from notion_zap.apps.prop_matcher.struct import Processor
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter
from notion_zap.cli.editors import PageRow, Database
from notion_zap.cli.structs import DatePropertyValue


class DateProcessorByCreatedTime(Processor):
    def __init__(self, root):
        super().__init__(root)
        self.get_date = DateGetterFromDateValue(self.root[MyBlock.dates])
        self.no_replace = True
        self.hour_offset = -5

    def __call__(self):
        for row, tag_dates in self.iter_args():
            if self.no_replace and has_relation(row, tag_dates):
                continue
            date_val = self.get_date_val(row)
            if date := self.get_date(date_val):
                set_relation(row, date, tag_dates)

    def get_date_val(self, row: PageRow):
        dom_idx: DatePropertyValue = row.read_key_alias('auto_datetime')
        date_val = dom_idx.start + dt.timedelta(hours=self.hour_offset)
        return date_val

    def iter_args(self):
        for _, table in self.bs.filtered_pick('dates'):
            for row in table.rows:
                yield row, 'dates'
        for _, table in self.bs.filtered_pick('dates', 'earliest_ref'):
            for row in table.rows:
                if row.read_key_alias('is_book') and row.read_key_alias('no_exp'):
                    continue
                yield row, 'dates'
        for _, table in self.bs.pick('dates_created'):
            for row in table.rows:
                yield row, 'dates_created'


class DateGetterFromDateValue:
    def __init__(self, dates: Database):
        self.dates = dates
        self.dates_by_title = self.dates.rows.index_by_tag('title')

    def __call__(self, date_val: Union[dt.date, dt.datetime]):
        if tar := self.find_tar_by_date(date_val):
            return tar
        return self.create_tar_by_date(date_val)

    def find_tar_by_date(self, date_val: Union[dt.date, dt.datetime]):
        date_handler = DateFormatter(date_val)
        tar_idx = date_handler.stringify_date()
        if tar := self.dates_by_title.get(tar_idx):
            return tar
        if tar := query_unique_page_by_idx(self.dates, tar_idx, 'title', 'title'):
            return tar
        return None

    def create_tar_by_date(self, date_val: Union[dt.date, dt.datetime]):
        tar = self.dates.rows.open_new_page()
        date_handler = DateFormatter(date_val)

        tar_idx = date_handler.stringify_date()
        tar.write(key_alias='title', value=tar_idx)

        date_range = DatePropertyValue(date_handler.date)
        tar.write_date(key_alias='date_manual', value=date_range)
        return tar.save()
