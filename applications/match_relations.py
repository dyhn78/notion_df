from collections.abc import Callable
from typing import Union
from abc import abstractmethod
import datetime
from datetime import datetime as datetimeclass

from notion_client import Client, AsyncClient

from interface.requests.edit import DatabaseUpdate, DatabaseCreate
from interface.parser.databases import PageListParser as PLParser
from interface.parser.pages import PagePropertyParser as PageParser
from interface.requests.structures import Requestor


class Applications:
    requests_queue = []
    reprocess_queue = []

    @abstractmethod
    def process(self, dom: PageParser):
        pass

    @staticmethod
    def append_requests(task: Requestor):
        Applications.requests_queue.append(task)

    @staticmethod
    def append_reprocess(task: tuple):
        Applications.reprocess_queue.append(task)


class MatchbyReference(Applications):
    def __init__(self, notion: Union[Client, AsyncClient], domain: PLParser, reference: PLParser,
                 domain_to_target: str, domain_to_reference: str, reference_to_target: str):
        self.notion = notion
        self.domain = domain
        self.reference = reference
        self.domain_to_target = domain_to_target
        self.domain_to_reference = domain_to_reference
        self.reference_to_target = reference_to_target

    def process(self, dom: PageParser):
        ref_id = dom.props[self.domain_to_reference]
        ref_props = self.reference.dict_by_id[ref_id]
        tar_id = ref_props[self.reference_to_target]

        dom_patch = DatabaseUpdate(self.notion, dom.id)
        dom_patch.props.add_relation(self.domain_to_target, [tar_id])
        self.append_requests(dom_patch)


class MatchbyTitle(Applications):
    def __init__(self, notion: Union[Client, AsyncClient], domain: PLParser, target: PLParser,
                 domain_to_target: str, dom_function: Callable):
        self.notion = notion
        self.domain = domain
        self.target = target
        self.domain_to_target = domain_to_target
        self.dom_function = dom_function

    def process(self, dom: PageParser):
        tar_title = self.dom_function(dom.title)
        if tar_title not in self.target.title_to_id:
            return tar_title
        else:
            tar_id = self.target.title_to_id[tar_title]
            dom_patch = DatabaseUpdate(self.notion, dom.id)
            dom_patch.props.add_relation(self.domain_to_target, [tar_id])
            self.append_requests(dom_patch)
            return False


class MatchCreatebyTitle(MatchbyTitle):
    def __init__(self, notion: Union[Client, AsyncClient], domain: PLParser, target: PLParser,
                 domain_to_target: str, dom_function: Callable, target_id: str):
        super().__init__(notion, domain, target, domain_to_target, dom_function)
        self.target_id = target_id

    def process(self, dom: PageParser):
        tar_title = super().process(dom)
        if not tar_title:
            return
        tar_patch = DatabaseCreate(self.notion, self.target_id)
        tar_patch.props.add_title(tar_title)
        self.append_reprocess((self.process, dom))


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
