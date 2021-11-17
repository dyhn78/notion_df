from __future__ import annotations
import datetime
from datetime import datetime as datetimecl, date as datecl
from typing import Union, Optional

from ..config import TIME_ZONE


class DateRange:
    TIME_ZONE = TIME_ZONE

    def __init__(self, start_date: Optional[Union[datetimecl, datecl]] = None,
                 end_date: Optional[Union[datetimecl, datecl]] = None):
        if start_date is None and end_date is not None:
            start_date, end_date = end_date, start_date
        self.start = self.__encode(start_date)
        self.end = self.__encode(end_date)

    def __encode(self, date: Optional[Union[datetimecl, datecl]])\
            -> Union[datetimecl, datecl, None]:
        # noinspection PyTypeChecker
        if isinstance(date, datetimecl):
            return date + datetime.timedelta(hours=self.TIME_ZONE)
        elif isinstance(date, datecl):
            return datetimecl.combine(date, datetimecl.min.time())
        else:
            return None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '{' + f"start: {str(self.start)}, end: {str(self.end)}" + '}'

    def __gt__(self, other: DateRange):
        return (self.start, self.end) > (other.start, other.end)

    def __eq__(self, other: DateRange):
        return (self.start, self.end) == (other.start, other.end)

    def __lt__(self, other: DateRange):
        return (self.start, self.end) < (other.start, other.end)

    @classmethod
    def from_isoformat(cls, start_datestring: str,
                       end_datestring=''):
        start = datetimecl.fromisoformat(start_datestring)
        if end_datestring:
            end = datetimecl.fromisoformat(end_datestring)
        else:
            end = None
        return cls(start, end)

    def make_isoformat(self):
        res = dict(start=self.start.isoformat())
        if self.end is not None:
            res.update(end=self.end.isoformat())
        return res
