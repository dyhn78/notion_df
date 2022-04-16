import datetime as dt
from typing import Optional


class DateRangeIterator:
    def __init__(self, year_range: Optional[tuple[int, int]] = None):
        self.year_range = year_range
        if year_range:
            self.min_date = dt.date(year_range[0], 1, 1)
            self.max_date = dt.date(year_range[1], 1, 1)

    def __iter__(self):
        if self.year_range is None:
            return
        date_val = self.min_date
        while date_val < self.max_date:
            yield date_val
            date_val += dt.timedelta(days=1)