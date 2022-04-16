from __future__ import annotations

from typing import Optional

from notion_zap.apps.prop_matcher.struct import EditorBase
from notion_zap.apps.prop_matcher.matchers.fill_date import DateIntroducer
from notion_zap.apps.prop_matcher.matchers.fill_week import PeriodIntroducer
from notion_zap.apps.prop_matcher.matchers.get_date_by_created_time import DateGetterFromDateValue
from notion_zap.apps.prop_matcher.matchers.get_week_by_manual_value import PeriodGetterFromDateValue
from notion_zap.apps.prop_matcher.utils.date_range_iterator import DateRangeIterator


class CalendarBuildController:
    def __init__(self, disable_overwrite=False, fetch_empties=True,
                 year_range: Optional[tuple[int, int]] = None):
        self.bs = EditorBase()
        self.date_range = (
            DateRangeIterator(year_range) if year_range else None)
        self.fetch = CalendarBuildFetcher(self.bs, self.date_range, fetch_empties)
        self.disable_overwrite = disable_overwrite

    def execute(self):
        self.fetch()
        self.introduce_pages()
        self.create_if_not_found(self.date_range)
        self.bs.save()

    def introduce_pages(self):
        introduce_date = DateIntroducer(self.disable_overwrite)
        for date in self.bs.dates.rows:
            introduce_date(date, None)
        introduce_period = PeriodIntroducer(self.disable_overwrite)
        for period in self.bs.periods.rows:
            introduce_period(period, None)

    def create_if_not_found(self, date_range: DateRangeIterator):
        create_date_if_not_found = DateGetterFromDateValue(self.bs.periods)
        for date_val in date_range:
            create_date_if_not_found(date_val)
        create_period_if_not_found = PeriodGetterFromDateValue(self.bs.periods)
        for date_val in date_range:
            create_period_if_not_found(date_val)


class CalendarBuildFetcher:
    MAX_REQUEST_SIZE = 50

    def __init__(self, bs: EditorBase,
                 year_range: Optional[tuple[int, int]],
                 empties=True,
                 request_size=0):
        self.bs = bs
        self.bs.root.exclude_archived = True
        self.request_size = request_size
        self.year_range = year_range
        self.date_range = DateRangeIterator(year_range)
        self.empties = empties

    def __call__(self):
        for table, tag_dateval in [
            (self.bs.dates, 'dateval_manual'),
            (self.bs.periods, 'manual_date_range')
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


class CalendarEditorBase(EditorBase):
    MAX_REQUEST_SIZE = 50

    def __init__(self,
                 year_range: Optional[tuple[int, int]],
                 empties=True,
                 request_size=0):
        super().__init__()
        self.root.exclude_archived = True
        self.request_size = request_size
        self.year_range = year_range
        self.date_range = DateRangeIterator(year_range)
        self.empties = empties

    def fetch_all(self):
        query = self.dates.open_query()
        ft = query.open_filter()
        frame = query.filter_manager_by_tags.date('dateval_manual')
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

        query = self.periods.open_query()
        ft = query.open_filter()
        frame = query.filter_manager_by_tags.date('manual_date_range')
        if self.empties:
            ft |= frame.is_empty()
        if self.year_range:
            ft |= (
                frame.on_or_after(self.date_range.min_date)
                & frame.before(self.date_range.max_date)
            )
        query.push_filter(ft)
        if not query.execute(self.request_size):
            query = self.periods.rows.open_query()
            query.execute(1)
