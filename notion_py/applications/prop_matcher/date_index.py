import datetime
from datetime import datetime as datetimeclass

from notion_py.interface import TypeName


class ProcessTimeProperty:
    korean_weekday = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]

    def __init__(self, date_time: datetimeclass):
        self.datetime = date_time
        self.date = self.datetime.date()

    def add_timedelta(self, hours: int):
        self.datetime = self.datetime + datetime.timedelta(hours=hours)
        self.date = self.datetime.date()

    def strf_dig6(self):
        return self.date.strftime("%y%m%d")

    def strf_dig6_and_weekday(self):
        dayname = self.korean_weekday[self.date.isoweekday() % 7]
        return f'{self.date.strftime("%y%m%d")} {dayname}'

    def strf_year_and_week(self):
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


class DatePageProcessor:
    @staticmethod
    def get_title(date_index: TypeName.date_format):
        date_handler = ProcessTimeProperty(date_index.start)
        date_handler.add_timedelta(-5)
        return date_handler.strf_dig6_and_weekday()


class PeriodPageProcessor:
    @staticmethod
    def get_title(date_index: TypeName.date_format):
        date_handler = ProcessTimeProperty(date_index.start)
        date_handler.add_timedelta(-5)
        return date_handler.strf_year_and_week()

    @staticmethod
    def writer(prop_key: str):
        def wrapper(page: TypeName.tabular_page, date_index: TypeName.date_format):
            date_handler = ProcessTimeProperty(date_index.start)
            date_handler.add_timedelta(-5)
            date_range = TypeName.date_format(
                start_date=date_handler.first_day_of_week(),
                end_date=date_handler.last_day_of_week()
            )
            page.props.write_date_at(prop_key, date_range)
        return wrapper


if __name__ == '__main__':
    print(datetimeclass.fromisocalendar(2021, 1, 1))

    # someday = datetimeclass.fromisoformat('2021-07-01T00:00:00.000+09:00')
    # print(someday.hour)
