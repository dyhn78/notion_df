from datetime import datetime as datetimeclass, date as dateclass
from typing import Union

from notion_py.gateway.write.property.unit import \
    RichTextUnitWriter, SimpleUnitWriter, BasicPageTitleWriter


class PagePropertyRichAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self):
        res = BasicPageTitleWriter('title')
        return self.caller.unpack()


class PagePropertyPlainAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self, value):
        return self.caller.unpack()


class TabularPagePropertyRichAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self, prop_name: str):
        return self.caller.unpack()

    def text(self, prop_name: str):
        return self.caller.unpack()


class TabularPagePropertyPlainAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self, prop_name: str, value: str):
        return self.caller.unpack()

    def text(self, prop_name: str, value: str):
        return self.caller.unpack()

    def date(self, prop_name: str,
             start_date: Union[datetimeclass, dateclass], end_date=None):
        return self.caller.unpack()

    def url(self, prop_name: str, value: str):
        return self.caller.unpack()

    def email(self, prop_name: str, value: str):
        return self.caller.unpack()

    def phone_number(self, prop_name: str, value: str):
        return self.caller.unpack()

    def number(self, prop_name: str, value: Union[int, float]):
        return self.caller.unpack()

    def checkbox(self, prop_name: str, value: bool):
        return self.caller.unpack()

    def select(self, prop_name: str, value: str):
        return self.caller.unpack()

    def files(self, prop_name: str, value: str):
        return self.caller.unpack()

    def people(self, prop_name: str, value: str):
        return self.caller.unpack()

    def multi_select(self, prop_name: str, values: list[str]):
        return self.caller.unpack()

    def relation(self, prop_name: str, page_ids: list[str]):
        return self.caller.unpack()
