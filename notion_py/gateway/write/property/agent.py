from datetime import datetime as datetimeclass, date as dateclass
from typing import Union

from notion_py.gateway.write.property.unit import \
    RichTextUnitWriter, SimpleUnitWriter, BasicPageTitleWriter


class PagePropertyRichAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self):
        res = BasicPageTitleWriter('title')
        return self.caller.apply(res)


class PagePropertyPlainAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self, value):
        return self.caller.apply(BasicPageTitleWriter('title', value))


class TabularPagePropertyRichAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self, prop_name: str):
        return self.caller.apply(RichTextUnitWriter('title', prop_name))

    def text(self, prop_name: str):
        return self.caller.apply(RichTextUnitWriter('rich_text', prop_name))


class TabularPagePropertyPlainAgent:
    def __init__(self, caller):
        self.caller = caller

    def title(self, prop_name: str, value: str):
        return self.caller.apply(RichTextUnitWriter('title', prop_name, value))

    def text(self, prop_name: str, value: str):
        return self.caller.apply(RichTextUnitWriter('rich_text', prop_name, value))

    def date(self, prop_name: str,
             start_date: Union[datetimeclass, dateclass], end_date=None):
        return self.caller.apply(SimpleUnitWriter.date(prop_name, start_date, end_date))

    def url(self, prop_name: str, value: str):
        return self.caller.apply(SimpleUnitWriter.url(prop_name, value))

    def email(self, prop_name: str, value: str):
        return self.caller.apply(SimpleUnitWriter.email(prop_name, value))

    def phone_number(self, prop_name: str, value: str):
        return self.caller.apply(SimpleUnitWriter.phone_number(prop_name, value))

    def number(self, prop_name: str, value: Union[int, float]):
        return self.caller.apply(SimpleUnitWriter.number(prop_name, value))

    def checkbox(self, prop_name: str, value: bool):
        return self.caller.apply(SimpleUnitWriter.checkbox(prop_name, value))

    def select(self, prop_name: str, value: str):
        return self.caller.apply(SimpleUnitWriter.select(prop_name, value))

    def files(self, prop_name: str, value: str):
        return self.caller.apply(SimpleUnitWriter.files(prop_name, value))

    def people(self, prop_name: str, value: str):
        return self.caller.apply(SimpleUnitWriter.people(prop_name, value))

    def multi_select(self, prop_name: str, values: list[str]):
        return self.caller.apply(SimpleUnitWriter.multi_select(prop_name, values))

    def relation(self, prop_name: str, page_ids: list[str]):
        return self.caller.apply(SimpleUnitWriter.relation(prop_name, page_ids))
