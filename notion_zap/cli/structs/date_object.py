from __future__ import annotations
import pytz
from datetime import datetime, date
from typing import Union, Optional


class DateObject:
    def __init__(self, start: Optional[Union[datetime, date]] = None,
                 end: Optional[Union[datetime, date]] = None):
        """default value of <start> and <end> is None."""
        if start is None and end is not None:
            start, end = end, start
        self.start = self.__add_explicit_tz(start)
        self.end = self.__add_explicit_tz(end)

    def is_emptylike(self):
        return self.start is None and self.end is None

    @staticmethod
    def __add_explicit_tz(date_val: Optional[Union[datetime, date]]) \
            -> Optional[Union[datetime, date]]:
        if isinstance(date_val, datetime):
            return date_val.astimezone()
        else:
            return date_val

    @classmethod
    def from_date_val(cls, date_val: Union[DateObject, datetime, date]):
        if isinstance(date_val, cls):
            return date_val
        else:
            return cls(date_val)

    @classmethod
    def from_isoformat(cls, start_datestring: str, end_datestring=''):
        start = cls.__parse_isoformat(start_datestring)
        end = cls.__parse_isoformat(end_datestring)
        return cls(start, end)

    @classmethod
    def from_utc_isoformat(cls, start_datestring: str, end_datestring=''):
        vals = []
        for datestr in [start_datestring, end_datestring]:
            date_val = cls.__parse_isoformat(datestr)
            if date_val:
                date_val = date_val.replace(tzinfo=pytz.UTC).astimezone()
                vals.append(date_val)
            else:
                vals.append(None)
        return cls(*vals)

    @staticmethod
    def __parse_isoformat(datestring: str):
        if not datestring:
            return None
        try:
            return date.fromisoformat(datestring)
        except ValueError:
            return datetime.fromisoformat(datestring)

    def isoformat(self):
        res = {}
        if self.start is not None:
            res.update(start=self.start.isoformat())
        if self.end is not None:
            res.update(end=self.to_datetime(self.end).isoformat())
        return res

    @property
    def start_date(self) -> Union[date, None]:
        return self.to_date(self.start)

    @property
    def end_date(self) -> Union[date, None]:
        return self.to_date(self.end)

    @property
    def start_dt(self) -> Union[datetime, None]:
        return self.to_datetime(self.start)

    @property
    def end_dt(self) -> Union[datetime, None]:
        return self.to_datetime(self.end)

    @staticmethod
    def to_datetime(date_val: Union[datetime, date]):
        if isinstance(date_val, date):
            date_val = datetime.combine(date_val, datetime.min.time())
        return date_val

    @staticmethod
    def to_date(date_val: Union[datetime, date]):
        if isinstance(date_val, datetime):
            date_val = date_val.date()
        return date_val

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '{' + f"start: {str(self.start)}, end: {str(self.end)}" + '}'

    def __gt__(self, other: Union[DateObject, datetime, date]):
        if isinstance(other, DateObject):
            return (self.start, self.end) > (other.start, other.end)
        else:
            return self.start > self.to_datetime(other)

    def __eq__(self, other: Union[DateObject, datetime, date]):
        if isinstance(other, DateObject):
            return (self.start, self.end) == (other.start, other.end)
        else:
            return self.start == self.to_datetime(other)

    def __lt__(self, other: Union[DateObject, datetime, date]):
        if isinstance(other, DateObject):
            return (self.start, self.end) < (other.start, other.end)
        else:
            return self.start < self.to_datetime(other)
