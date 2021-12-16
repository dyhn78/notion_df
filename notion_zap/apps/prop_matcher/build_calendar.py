from __future__ import annotations

from .managers import *
from .common.struct import EditorManager, EditorBase
from .managers.calendar import DateTargetFiller, CalendarDateRange, PeriodTargetFiller


class CalendarController:
    def __init__(self, disable_overwrite=False, fetch_empties=True,
                 fetch_year_range: Optional[tuple[int, int]] = None):
        self.disable_overwrite = disable_overwrite
        self.fetch_empties = fetch_empties
        self.fetch_year_range = (
            CalendarDateRange(fetch_year_range) if fetch_year_range else None)
        self.bs = CalendarEditorBase(
            fetch_year_range, empties=fetch_empties, request_size=0)

    def execute(self):
        self.bs.fetch_all()
        agents: list[EditorManager] = [
            DateTargetFiller(self.bs, self.disable_overwrite,
                             self.fetch_year_range),
            PeriodTargetFiller(self.bs, self.disable_overwrite,
                               self.fetch_year_range)
        ]
        for agent in agents:
            agent.execute()
        self.bs.save()


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
        self.date_range = CalendarDateRange(year_range)
        self.empties = empties

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
        if not query.execute():
            self.dates.fetch(1)

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
        if not query.execute():
            self.periods.fetch(1)


