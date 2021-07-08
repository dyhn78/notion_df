import datetime
from datetime import datetime as datetimeclass


class ParseTimeProperty:
    korean_weekday = ["화요일", "수요일", "목요일", "금요일", "토요일", "일요일", "월요일"]

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
        year, week, weekday = self._augmented_iso_calendar()
        first_day_of_week = self.date + datetime.timedelta(days=-weekday)
        last_day_of_week = first_day_of_week + + datetime.timedelta(days=6)

        return (self.date.strftime("%y-%U주: ") +
                first_day_of_week.strftime("%y%m%d-") +
                last_day_of_week.strftime("%y%m%d"))

    def _augmented_iso_calendar(self):
        year, week, weekday = self.date.isocalendar()
        if weekday == 7:  # 일요일
            week, weekday = week + 1, weekday - 7
        return year, week, weekday


if __name__ == '__main__':
    print(datetimeclass.fromisocalendar(2021, 1, 1))

    # someday = datetimeclass.fromisoformat('2021-07-01T00:00:00.000+09:00')
    # print(someday.hour)
