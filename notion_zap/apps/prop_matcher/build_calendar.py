from __future__ import annotations

from datetime import date

from .matchers import *
from .common.struct import Matcher, LocalBase


class CalendarController:
    def __init__(self, disable_overwrite=False, fetch_empties=True,
                 fetch_year_range: Optional[tuple[int, int]] = None):
        self.disable_overwrite = disable_overwrite
        self.fetch_empties = fetch_empties
        self.fetch_year_range = (
            CalendarDateRange(fetch_year_range) if fetch_year_range else None)
        self.bs = CalendarBase(fetch_year_range, empties=fetch_empties, request_size=0)

    def execute(self):
        self.bs.fetch_all()
        agents: list[Matcher] = [
            DateTargetFiller(self.bs, self.disable_overwrite,
                             self.fetch_year_range),
            PeriodTargetAutoFiller(self.bs, self.disable_overwrite,
                                   self.fetch_year_range)
        ]
        for agent in agents:
            agent.execute()
        self.bs.save()


class CalendarBase(LocalBase):
    MAX_REQUEST_SIZE = 50

    def __init__(self,
                 year_range: Optional[tuple[int, int]],
                 empties=True,
                 request_size=0):
        super().__init__()
        self.root.exclude_archived = True
        self.request_size = request_size
        self.year_range = year_range
        self.date_range = CalendarDateRange(year_range)
        self.empties = empties

    def fetch_all(self):
        query = self.dates.open_query()
        ft = query.open_filter()
        frame = query.filter_maker.date_at('manual_date')
        if self.empties:
            ft |= frame.is_empty()
        if self.year_range:
            ft |= (
                frame.on_or_after(self.date_range.min_date)
                & frame.before(self.date_range.max_date)
            )
        query.push_filter(ft)
        if not query.execute(self.request_size):
            self.dates.fetch(1)

        query = self.periods.open_query()
        ft = query.open_filter()
        frame = query.filter_maker.date_at('manual_date_range')
        if self.empties:
            ft |= frame.is_empty()
        if self.year_range:
            ft |= (
                frame.on_or_after(self.date_range.min_date)
                & frame.before(self.date_range.max_date)
            )
        query.push_filter(ft)
        if not query.execute(self.request_size):
            self.periods.fetch(1)


class CalendarDateRange:
    def __init__(self, year_range: Optional[tuple[int, int]] = None):
        self.year_range = year_range
        if year_range:
            self.min_date = date(year_range[0], 1, 1)
            self.max_date = date(year_range[1], 1, 1)

    def iter_date(self):
        date_val = self.min_date
        while date_val < self.max_date:
            yield date_val
            date_val += dt.timedelta(days=1)
