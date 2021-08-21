from datetime import datetime as datetimeclass, date as dateclass
from typing import Optional, Union


class DateFormat:
    def __init__(self, start_date: Optional[Union[datetimeclass, dateclass]] = None,
                 end_date: Optional[Union[datetimeclass, dateclass]] = None):
        if start_date is None and end_date is not None:
            start_date, end_date = end_date, start_date
        self.start_date = start_date
        self.end_date = end_date


def make_isoformat(value: DateFormat):
    start, end = value.start_date, value.end_date
    res = dict(start=start.isoformat())
    if end is not None:
        res.update(end=end.isoformat())
    return res