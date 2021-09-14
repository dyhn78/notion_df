import datetime
from datetime import datetime as datetimeclass

from notion_py.interface import TypeName


class ProcessTimeProperty:
    korean_weekday = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]

    def __init__(self, date_time: datetimeclass, plain_date=False):
        self.datetime = date_time + datetime.timedelta(hours=9)
        if plain_date:
            self.date = self.datetime.date()
        else:
            self.date = (self.datetime + datetime.timedelta(hours=-5)).date()

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
    def get_title(date: TypeName.date_format):
        return ProcessTimeProperty(date.start, plain_date=True).strf_dig6_and_weekday()


class PeriodPageProcessor:
    @staticmethod
    def get_title(date: TypeName.date_format):
        base = ProcessTimeProperty(date.start, plain_date=True)
        return base.strf_year_and_week()

    @staticmethod
    def writer(prop_key: str):
        def wrapper(page: TypeName.tabular_page, index_value: TypeName.date_format):
            base = ProcessTimeProperty(index_value.start, plain_date=True)
            daterange = TypeName.date_format(
                start_date=base.first_day_of_week(),
                end_date=base.last_day_of_week()
            )
            page.props.write_date_at(prop_key, daterange)
        return wrapper


if __name__ == '__main__':
    print(datetimeclass.fromisocalendar(2021, 1, 1))

    # someday = datetimeclass.fromisoformat('2021-07-01T00:00:00.000+09:00')
    # print(someday.hour)
