import datetime as dt
from typing import Union


class DateFormatter:
    korean_weekday = \
        ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]

    def __init__(self, date_time: Union[dt.datetime, dt.date]):
        if isinstance(date_time, dt.datetime):
            date_time = date_time.date()
        self.date: dt.date = date_time

    def stringify_date(self):
        return self._strf_dig6_and_weekday()

    @classmethod
    def from_date_title(cls, strf: str):
        return cls._from_dig6(strf)

    def _strf_dig6(self):
        """예) 210101"""
        return self.date.strftime("%y%m%d")

    def _strf_dig6_and_weekday(self):
        """예) 210101 금요일"""
        dayname = self.korean_weekday[self.date.isoweekday() % 7]
        return f'{self.date.strftime("%y%m%d")} {dayname}'

    @classmethod
    def _from_dig6(cls, strf: str):
        year = 2000 + int(strf[:2])
        month = int(strf[2:4])
        date = int(strf[4:6])
        return cls(dt.date(year, month, date))

    def stringify_week(self):
        return self._strf_year_and_week()

    @classmethod
    def from_week_title(cls, strf: str):
        return cls._from_strf_year_and_week(strf)

    def _strf_year_and_week(self):
        return self.date.strftime("%Y/%U")

    @classmethod
    def _from_strf_year_and_week(cls, strf: str):
        year = int(strf[:2])
        month = int(strf[3:5])
        return cls(dt.datetime.strptime(f'{year} {month} 0', "%y %U %w"))

    def _strf_year_and_week_verbose(self):
        """예) 2021년 47주: 1121-1126"""
        return (self.date.strftime("%Y년 %U주: ") +
                self.first_day_of_week().strftime("%m%d-") +
                self.last_day_of_week().strftime("%m%d"))

    @classmethod
    def _from_strf_year_and_week_verbose(cls, strf: str):
        year = int(strf[:4])

        # 시작 날짜
        dash_idx = strf.index('-')
        month = int(strf[dash_idx - 4: dash_idx - 2])
        date = int(strf[dash_idx - 2: dash_idx])
        return cls(dt.date(year, month, date))

    def first_day_of_week(self):
        year, week, weekday = self._augmented_iso_calendar()
        return self.date + dt.timedelta(days=-weekday)

    def last_day_of_week(self):
        return self.first_day_of_week() + + dt.timedelta(days=6)

    def _augmented_iso_calendar(self):
        year, week, weekday = self.date.isocalendar()
        if weekday == 7:  # 일요일
            week, weekday = week + 1, weekday - 7
        return year, week, weekday


if __name__ == '__main__':
    print(dt.datetime.fromisocalendar(2021, 1, 1))

    # someday = datetimecl.fromisoformat('2021-07-01T00:00:00.000+09:00')
    # print(someday.hour)
