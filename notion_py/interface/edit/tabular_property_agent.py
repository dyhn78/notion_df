from datetime import datetime as datetimeclass, date as dateclass
from typing import Union, Callable

from notion_py.gateway.write.property.unit import \
    SimpleUnitWriter, RichTextUnitWriter, BasicPageTitleWriter


class PropertyAgent:
    def __init__(self, caller, prop_name: str):
        self.caller = caller
        self.prop_name = prop_name


class RichPropertyAgent(PropertyAgent):
    def title(self):
        carrier = RichTextUnitWriter('title', self.prop_name)
        self.caller.apply(self.prop_name, carrier)

    def text(self):
        carrier = RichTextUnitWriter('rich_text', self.prop_name)
        self.caller.apply(self.prop_name, carrier)


class PlainPropertyAgent(PropertyAgent):
    def title(self, value: str):
        carrier = RichTextUnitWriter('title', self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def text(self, value: str):
        carrier = RichTextUnitWriter('rich_text', self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def date(self, start_date: Union[datetimeclass, dateclass], end_date=None):
        carrier = SimpleUnitWriter.date(self.prop_name, start_date, end_date)
        self.caller.apply(self.prop_name, carrier)

    def url(self, value: str):
        carrier = SimpleUnitWriter.url(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def email(self, value: str):
        carrier = SimpleUnitWriter.email(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def phone_number(self, value: str):
        carrier = SimpleUnitWriter.phone_number(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def number(self, value: Union[int, float]):
        carrier = SimpleUnitWriter.number(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def checkbox(self, value: bool):
        carrier = SimpleUnitWriter.checkbox(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def select(self, value: str):
        carrier = SimpleUnitWriter.select(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def files(self, value: str):
        carrier = SimpleUnitWriter.files(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def people(self, value: str):
        carrier = SimpleUnitWriter.people(self.prop_name, value)
        self.caller.apply(self.prop_name, carrier)

    def multi_select(self, values: list[str]):
        carrier = SimpleUnitWriter.multi_select(self.prop_name, values)
        self.caller.apply(self.prop_name, carrier)

    def relation(self, page_ids: list[str]):
        carrier = SimpleUnitWriter.relation(self.prop_name, page_ids)
        self.caller.apply(self.prop_name, carrier)


class PagePropertyRichAgent:
    @staticmethod
    def title():
        return BasicPageTitleWriter('title')


class PagePropertyPlainAgent:
    @staticmethod
    def title(value):
        return BasicPageTitleWriter('title', value)