from __future__ import annotations

import datetime as dt
from typing import Union

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.struct import Processor
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter
from notion_zap.apps.prop_matcher.utils.relation_prop_helpers import (
    has_relation, set_relation, query_unique_page_by_idx)
from notion_zap.cli.editors import PageRow, Database
from notion_zap.cli.structs import DatePropertyValue


class DateProcessorByCreatedTime(Processor):
    def __init__(self, root, option):
        super().__init__(root, option)
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
        dom_idx: DatePropertyValue = row.read_key_alias('datetime_auto')
        date_val = dom_idx.start + dt.timedelta(hours=self.hour_offset)
        return date_val

    def iter_args(self):
        for table in self.root.get_blocks(self.option.filter_key('dates_created')):
            for row in table.rows:
                yield row, 'dates_created'
        for table in self.root.get_blocks(self.option.filter_pair('dates')):
            for row in table.rows:
                yield row, 'dates'
        for table in self.root.get_blocks(
                self.option.filter_pair('dates_begin', 'ignore_book_with_no_exp')):
            for row in table.rows:
                if not row.read_key_alias('no_exp'):
                    yield row, 'dates'


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
        tar.write_date(key_alias='manual_date', value=date_range)
        return tar.save()
