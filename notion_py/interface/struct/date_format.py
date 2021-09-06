from datetime import datetime as datetimeclass, date as dateclass
from typing import Optional, Union


class DateFormat:
    def __init__(self, start_date: Optional[Union[datetimeclass, dateclass]] = None,
                 end_date: Optional[Union[datetimeclass, dateclass]] = None):
        if start_date is None and end_date is not None:
            start_date, end_date = end_date, start_date
        self.start = start_date
        self.end = end_date

    def make_isoformat(self):
        res = dict(start=self.start.isoformat())
        if end is not None:
            res.update(end=self.end.isoformat())
        return res
