from collections.abc import Callable
import datetime
from datetime import datetime as datetimeclass

from interface.requests.edit import DatabaseUpdate as DBUpdateHandler
from interface.response.parse import PageListParser as PLParser, PageParser


def clone_from_base(dom: PageParser, base: PLParser,
                    domain_to_target: str, domain_to_base: str, base_to_target: str):
    bs_id = dom.props[domain_to_base]
    bs_props = base.dict_by_id[bs_id]
    tar_id = bs_props[base_to_target]

    dom_patch = DBUpdateHandler(dom.id)
    dom_patch.append_relation(dom.props[domain_to_target], tar_id)
    return dom_patch


def find_by_title(dom: PageParser, target: PLParser,
                  domain_to_target: str, dom_function: Callable):
    tar_title = dom_function(dom.title)
    try:
        tar_id = target.title_to_id[tar_title]
        dom_patch = DBUpdateHandler(dom.id)
        dom_patch.append_relation(dom.props[domain_to_target], tar_id)
        return dom_patch
    except KeyError:
        # TODO : create_handler 만들어 추가
        return tar_title


class ParseTimeProperty:
    korean_dayname = ["일요일", "월요일", "화요일", "수요일", "목요일", "금요일", "토요일"]

    def __init__(self, date: datetimeclass):
        self.plain_date = date.date()
        self.true_date = (date + datetime.timedelta(hours=-5)).date()

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
