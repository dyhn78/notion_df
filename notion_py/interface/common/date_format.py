import datetime
from datetime import datetime as datetimeclass, date as dateclass
from typing import Optional, Union


class DateFormat:
    TIME_ZONE = 9  # SEOUL

    def __init__(self, start_date: Union[datetimeclass, dateclass, None] = None,
                 end_date: Union[datetimeclass, dateclass, None] = None):
        if start_date is None and end_date is not None:
            start_date, end_date = end_date, start_date
        self.start = self.__encode(start_date)
        self.end = self.__encode(end_date)

    def __encode(self, date: Union[datetimeclass, dateclass, None])\
            -> Union[datetimeclass, dateclass, None]:
        if date is not None:
            return date + datetime.timedelta(hours=self.TIME_ZONE)
        else:
            return None

    def __repr__(self):
        return self.__str__()

    def __str__(self):
        return '{' + f"start: {str(self.start)}, end: {str(self.end)}" + '}'

    @classmethod
    def from_isoformat(cls, start_datestring: str,
                       end_datestring=''):
        start = datetimeclass.fromisoformat(start_datestring)
        if end_datestring:
            end = datetimeclass.fromisoformat(end_datestring)
        else:
            end = None
        return cls(start, end)

    def make_isoformat(self):
        res = dict(start=self.start.isoformat())
        if self.end is not None:
            res.update(end=self.end.isoformat())
        return res
