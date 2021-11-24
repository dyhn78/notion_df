import datetime as dt
from datetime import datetime as datetime, date as date
from typing import Union


class DateHandler:
    korean_weekday = \
        ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]

    def __init__(self, date_time: Union[datetime, date]):
        if isinstance(date_time, datetime):
            date_time = date_time.date()
        self.date = date_time

    def strf_dig6(self):
        """예) 210101"""
        return self.date.strftime("%y%m%d")

    def strf_dig6_and_weekday(self):
        """예) 210101 금요일"""
        dayname = self.korean_weekday[self.date.isoweekday() % 7]
        return f'{self.date.strftime("%y%m%d")} {dayname}'

    def strf_year_and_week(self):
        """예) 2021년 47주: 1121-1126"""
        return (self.date.strftime("%Y년 %U주: ") +
                self.first_day_of_week().strftime("%m%d-") +
                self.last_day_of_week().strftime("%m%d"))

    def first_day_of_week(self):
        year, week, weekday = self._augmented_iso_calendar()
        return self.date + dt.timedelta(days=-weekday)

    def last_day_of_week(self):
        return self.first_day_of_week() + + dt.timedelta(days=6)

    @classmethod
    def from_strf_dig6(cls, strf: str):
        year = 2000 + int(strf[:2])
        month = int(strf[2:4])
        date_val = int(strf[4:6])
        return cls(date(year, month, date_val))

    @classmethod
    def from_strf_year_and_week(cls, strf: str):
        year = int(strf[:4])
        dash_idx = strf.index('-')
        month = int(strf[dash_idx - 4: dash_idx - 2])
        date_val = int(strf[dash_idx - 2: dash_idx])
        return cls(date(year, month, date_val))

    def _augmented_iso_calendar(self):
        year, week, weekday = self.date.isocalendar()
        if weekday == 7:  # 일요일
            week, weekday = week + 1, weekday - 7
        return year, week, weekday


if __name__ == '__main__':
    print(datetime.fromisocalendar(2021, 1, 1))

    # someday = datetimecl.fromisoformat('2021-07-01T00:00:00.000+09:00')
    # print(someday.hour)
