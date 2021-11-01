import datetime
from datetime import datetime as datetimeclass, date as dateclass
from typing import Union

from notion_py.interface.common import DateFormat


class ProcessTimeProperty:
    korean_weekday = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]

    def __init__(self, date_time: Union[datetimeclass, dateclass],
                 add_timedelta=0):
        """add_timedelta has effect only when argument was datetimeclass."""
        if isinstance(date_time, datetimeclass):
            date_time += datetime.timedelta(hours=add_timedelta)
            self.date = date_time.date()
        elif isinstance(date_time, dateclass):
            self.date = date_time

    def strf_dig6(self):
        """예) 210101"""
        return self.date.strftime("%y%m%d")

    def strf_dig6_and_weekday(self):
        """예) 210101 금요일"""
        dayname = self.korean_weekday[self.date.isoweekday() % 7]
        return f'{self.date.strftime("%y%m%d")} {dayname}'

    def strf_year_and_week(self):
        """예) 21"""
        return (self.date.strftime("%Y년 %U주: ") +
                self.first_day_of_week().strftime("%m%d-") +
                self.last_day_of_week().strftime("%m%d"))

    def first_day_of_week(self):
        year, week, weekday = self._augmented_iso_calendar()
        return self.date + datetime.timedelta(days=-weekday)

    def last_day_of_week(self):
        return self.first_day_of_week() + + datetime.timedelta(days=6)

    def _augmented_iso_calendar(self):
        year, week, weekday = self.date.isocalendar()
        if weekday == 7:  # 일요일
            week, weekday = week + 1, weekday - 7
        return year, week, weekday


if __name__ == '__main__':
    print(datetimeclass.fromisocalendar(2021, 1, 1))

    # someday = datetimeclass.fromisoformat('2021-07-01T00:00:00.000+09:00')
    # print(someday.hour)
