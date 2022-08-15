from __future__ import annotations

import datetime as dt
from typing import cast

from notion_zap.apps.myblock import MyBlock
from notion_zap.apps.prop_matcher.struct import Processor
from notion_zap.apps.prop_matcher.utils.date_formatter import DateFormatter
from notion_zap.apps.prop_matcher.utils.relation_prop_helpers import has_relation, set_relation, \
    query_unique_page_by_idx
from notion_zap.cli.blocks import PageRow, Database
from notion_zap.cli.core import DatePropertyValue


class WeekProcessorByManualDate(Processor):
    def __init__(self, root, option):
        super().__init__(root, option)
        self.tag_week = 'weeks'
        self.get_week = WeekRowGetterByManualDate(self.root[MyBlock.weeks])

    def __call__(self):
        tables = cast(list[Database], self.root.get_blocks(self.option.filter_pair('weeks', 'manual_date')))
        for table in tables:
            for row in table.rows:
                if has_relation(row, self.tag_week):
                    continue
                date = get_date(row, 'manual_date')
                if week := self.get_week(date):
                    set_relation(row, week, self.tag_week)


def get_date(date_row: PageRow, tag_manual_value):
    date_object: DatePropertyValue = date_row.read_key_alias(tag_manual_value)
    return date_object.start_date


class WeekRowGetterByManualDate:
    def __init__(self, periods: Database):
        self.periods = periods
        self.periods_by_title = self.periods.rows.index_by_tag('title')

    def __call__(self, date: dt.date):
        if tar := self.find_by_date(date):
            return tar
        return self.create_by_date(date)

    def find_by_date(self, date: dt.date):
        if not date:
            return None
        date_handler = DateFormatter(date)
        tar_idx = date_handler.stringify_week()
        if tar := self.periods_by_title.get(tar_idx):
            return tar
        if tar := query_unique_page_by_idx(self.periods, tar_idx, 'title', 'title'):
            return tar
        return None

    def create_by_date(self, date: dt.date):
        if not date:
            return None
        tar = self.periods.rows.open_new_page()
        date_handler = DateFormatter(date)

        tar_idx = date_handler.stringify_week()
        tar.write_title(key_alias='title', value=tar_idx)

        date_range = DatePropertyValue(start=date_handler.first_day_of_week(),
                                       end=date_handler.last_day_of_week())
        tar.write_date(key_alias='manual_date', value=date_range)
        return tar.save()
