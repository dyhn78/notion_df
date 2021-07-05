import datetime
from datetime import datetime as datetimeclass


class ParseTimeProperty:
    korean_dayname = ["월요일", "화요일", "수요일", "목요일", "금요일", "토요일", "일요일"]

    def __init__(self, date_string: str):
        self.datetime = datetimeclass.fromisoformat(date_string)
        self.plain_date = self.datetime.date()
        self.true_date = (self.datetime + datetime.timedelta(hours=-5)).date()

    def __date(self, plain=False):
        return self.plain_date if plain else self.true_date

    def dig6(self, plain=False):
        return self.__date(plain).strftime("%y%m%d")

    def dig6_and_dayname(self, plain=False):
        dayname = self.korean_dayname[self.__date(plain).weekday()]
        return f'{self.__date(plain).strftime("%y%m%d")} {dayname}'


"""
someday = datetimeclass.fromisoformat('2021-07-01T00:00:00.000+09:00')
print(someday.hour)
"""


