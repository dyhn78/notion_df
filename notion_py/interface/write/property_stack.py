from collections import defaultdict
from datetime import datetime as datetimeclass, date as dateclass
from pprint import pprint
from typing import Union, Optional

from notion_py.interface.structure import TwofoldDictStash
from .property_unit import PageProperty, SimplePageProperty, RichTextProperty


class BasicPagePropertyStack(TwofoldDictStash):
    def __init__(self, overwrite: bool):
        super().__init__()
        self.read = defaultdict(dict)
        self.overwrite = overwrite

    def apply(self):
        return {'properties': self._unpack()}

    def update_read(self, value: dict):
        self.read.update(**value)

    @property
    def write_rich(self):
        return PagePropertyRichAgent(self)

    @property
    def write(self):
        return PagePropertyPlainAgent(self)

    def stash(self, carrier: PageProperty) -> Optional[PageProperty]:
        if self._will_overwrite(carrier.prop_name):
            return super().stash(carrier)
        else:
            return None

    def _will_overwrite(self, prop_name: str):
        if self.overwrite:
            return True
        else:
            return self.read_empty_value(prop_name)

    def read_empty_value(self, prop_name: str) -> bool:
        value = self.read[prop_name]
        if type(value) == list:
            return self.read_empty_value(value[0])
        elif type(value) == str:
            return value not in ['', '.', '-']
        elif type(value) == int:
            return value not in [0, 1]
        else:
            return bool(value)


class PagePropertyRichAgent:
    def __init__(self, caller: BasicPagePropertyStack):
        self.caller = caller

    def title(self, prop_name: str):
        res = RichTextProperty('title', prop_name)
        self.caller.stash(res)
        return res


class PagePropertyPlainAgent:
    def __init__(self, caller: BasicPagePropertyStack):
        self.caller = caller

    def title(self, prop_name: str, value):
        return self.caller.stash(RichTextProperty.plain_form('title', prop_name, value))


class TabularPagePropertyStack(BasicPagePropertyStack):
    @property
    def write_rich(self):
        return TabularPagePropertyRichAgent(self)

    @property
    def write(self):
        return TabularPagePropertyPlainAgent(self)


class TabularPagePropertyRichAgent(PagePropertyRichAgent):
    def text(self, prop_name: str):
        res = RichTextProperty('rich_text', prop_name)
        self.caller.stash(RichTextProperty('rich_text', prop_name))
        return res


class TabularPagePropertyPlainAgent(PagePropertyPlainAgent):
    def text(self, prop_name: str, value):
        return self.caller.stash(RichTextProperty.plain_form('rich_text', prop_name, value))

    def date(self, prop_name: str, start_date: Union[datetimeclass, dateclass], end_date=None):
        return self.caller.stash(SimplePageProperty.date(prop_name, start_date, end_date))

    def number(self, prop_name: str, value):
        return self.caller.stash(SimplePageProperty.number(prop_name, value))

    def checkbox(self, prop_name: str, value):
        return self.caller.stash(SimplePageProperty.checkbox(prop_name, value))

    def select(self, prop_name: str, value):
        return self.caller.stash(SimplePageProperty.select(prop_name, value))

    def files(self, prop_name: str, value):
        return self.caller.stash(SimplePageProperty.files(prop_name, value))

    def people(self, prop_name: str, value):
        return self.caller.stash(SimplePageProperty.people(prop_name, value))

    def multi_select(self, prop_name: str, values: list[str]):
        return self.caller.stash(SimplePageProperty.multi_select(prop_name, values))

    def relation(self, prop_name: str, page_ids: list[str]):
        return self.caller.stash(SimplePageProperty.relation(prop_name, page_ids))
