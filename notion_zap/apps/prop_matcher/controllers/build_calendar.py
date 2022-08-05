from __future__ import annotations

from typing import Optional

from notion_zap.apps.config import MyBlock
from notion_zap.apps.prop_matcher.processors.conform_format import DateFormatConformer, \
    WeekFormatConformer
from notion_zap.apps.prop_matcher.processors.get_date_from_created_time import \
    DateGetterFromDateValue
from notion_zap.apps.prop_matcher.processors.get_week_from_manual_date import \
    WeekRowGetterFromManualDate
from notion_zap.apps.prop_matcher.struct import init_root
from notion_zap.apps.prop_matcher.utils.date_range_iterator import DateRangeIterator
from notion_zap.cli.core.base import Root


class CalendarBuildController:
    def __init__(self, disable_overwrite=False, fetch_empties=True,
                 year_range: Optional[tuple[int, int]] = None):
        self.root = init_root()
        self.date_range = (
            DateRangeIterator(year_range) if year_range else None)
        self.fetch = CalendarBuildFetcher(self.root, self.date_range, fetch_empties)
        self.disable_overwrite = disable_overwrite

    def execute(self):
        self.fetch()
        self.introduce_pages()
        self.create_if_not_found(self.date_range)
        self.root.save()

    def introduce_pages(self):
        introduce_date = DateFormatConformer(self.disable_overwrite)
        for date in self.root.dates.rows:
            introduce_date(date, None)
        introduce_period = WeekFormatConformer(self.disable_overwrite)
        for week in self.root[MyBlock.weeks].rows:
            introduce_period(week, None)

    def create_if_not_found(self, date_range: DateRangeIterator):
        create_date_if_not_found = DateGetterFromDateValue(self.root[MyBlock.weeks])
        for date_val in date_range:
            create_date_if_not_found(date_val)
        create_period_if_not_found = WeekRowGetterFromManualDate(self.root[MyBlock.weeks])
        for date_val in date_range:
            create_period_if_not_found(date_val)


class CalendarBuildFetcher:
    MAX_REQUEST_SIZE = 50

    def __init__(self, root: Root,
                 year_range: Optional[tuple[int, int]],
                 empties=True,
                 request_size=0):
        self.root = root
        self.root.exclude_archived = True
        self.request_size = request_size
        self.year_range = year_range
        self.date_range = DateRangeIterator(year_range)
        self.empties = empties

    def __call__(self):
        for table, tag_dateval in [
            (self.root[MyBlock.dates], 'manual_date'),
            (self.root[MyBlock.weeks], 'manual_date')
        ]:
            query = table.rows.open_query()
            ft = query.open_filter()
            frame = query.filter_manager_by_tags.date(tag_dateval)
            if self.empties:
                ft |= frame.is_empty()
            if self.year_range:
                ft |= (
                        frame.on_or_after(self.date_range.min_date)
                        & frame.before(self.date_range.max_date)
                )
            query.push_filter(ft)
            if query.execute(self.request_size):
                return

            query = table.rows.open_query()
            query.execute(1)


class CalendarMainEditorDepr:
    MAX_REQUEST_SIZE = 50

    def __init__(self,
                 year_range: Optional[tuple[int, int]],
                 empties=True,
                 request_size=0):
        super().__init__()
        self.root = init_root()
        self.request_size = request_size
        self.year_range = year_range
        self.date_range = DateRangeIterator(year_range)
        self.empties = empties
        self.weeks = self.root[MyBlock.weeks]
        self.dates = self.root[MyBlock.dates]

    def fetch_all(self):
        query = self.dates.open_query()
        ft = query.open_filter()
        frame = query.filter_manager_by_tags.date('manual_date')
        if self.empties:
            ft |= frame.is_empty()
        if self.year_range:
            ft |= (
                frame.on_or_after(self.date_range.min_date)
                & frame.before(self.date_range.max_date)
            )
        query.push_filter(ft)
        if not query.execute(self.request_size):
            query = self.dates.rows.open_query()
            query.execute(1)

        query = self.weeks.open_query()
        ft = query.open_filter()
        frame = query.filter_manager_by_tags.date('manual_date')
        if self.empties:
            ft |= frame.is_empty()
        if self.year_range:
            ft |= (
                frame.on_or_after(self.date_range.min_date)
                & frame.before(self.date_range.max_date)
            )
        query.push_filter(ft)
        if not query.execute(self.request_size):
            query = self.weeks.rows.open_query()
            query.execute(1)
