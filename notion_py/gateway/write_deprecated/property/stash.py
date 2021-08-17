from abc import ABCMeta
from collections import defaultdict
from datetime import datetime as datetimeclass, date as dateclass
from typing import Union, Optional

from ..twofold_stash import TwofoldDictStash
from .unit import \
    WritePageProperty, WriteSimplePageProperty, \
    WriteRichTextProperty, WriteTitleProperty


class PagePropertyStash(TwofoldDictStash, metaclass=ABCMeta):
    def __init__(self):
        super().__init__()
        self.read = defaultdict(dict)
        self._overwrite_parameter = True

    def apply(self) -> dict:
        return {'properties': self._unpack()}

    def set_overwrite(self, value: bool):
        self._overwrite_parameter = value

    def fetch(self, value: dict):
        self.read.update(**value)

    def stash(self, carrier: WritePageProperty) -> Optional[WritePageProperty]:
        if self._overwrite(carrier.prop_name):
            return super().stash(carrier)
        else:
            return None

    def _overwrite(self, prop_name: str):
        if self._overwrite_parameter:
            return True
        else:
            return self.read_empty_value(prop_name)

    def read_empty_value(self, prop_name: str) -> bool:
        value = self.read[prop_name]
        return self._is_empty_value(value)

    @classmethod
    def _is_empty_value(cls, value) -> bool:
        if type(value) == list:
            if bool(value):
                # TODO : fetch 가 정보를 read와 read_rich로 나누어 담는 기능이 구현되면,
                #  이 기능은 없애야 한다.
                return cls._is_empty_value(value[0])
            return True
        elif type(value) == bool:
            return value
        else:
            return str(value) in ['', '.', '-', '0', '1']


class BasicPagePropertyStash(PagePropertyStash):
    def __init__(self):
        super().__init__()
        self.write = PagePropertyPlainAgent(self)
        self.write_rich = PagePropertyRichAgent(self)


class PagePropertyRichAgent:
    def __init__(self, caller: BasicPagePropertyStash):
        self.caller = caller

    def title(self):
        res = WriteTitleProperty('title')
        return self.caller.stash(res)


class PagePropertyPlainAgent:
    def __init__(self, caller: BasicPagePropertyStash):
        self.caller = caller

    def title(self, value):
        return self.caller.stash(WriteTitleProperty('title', value))


class TabularPagePropertyStash(PagePropertyStash):
    def __init__(self):
        super().__init__()
        self.write = TabularPagePropertyPlainAgent(self)
        self.write_rich = TabularPagePropertyRichAgent(self)


class TabularPagePropertyRichAgent:
    def __init__(self, caller: TabularPagePropertyStash):
        self.caller = caller

    def title(self, prop_name: str):
        return self.caller.stash(WriteRichTextProperty('title', prop_name))

    def text(self, prop_name: str):
        return self.caller.stash(WriteRichTextProperty('rich_text', prop_name))


class TabularPagePropertyPlainAgent:
    def __init__(self, caller: TabularPagePropertyStash):
        self.caller = caller

    def title(self, prop_name: str, value: str):
        return self.caller.stash(WriteRichTextProperty('title', prop_name, value))

    def text(self, prop_name: str, value: str):
        return self.caller.stash(WriteRichTextProperty('rich_text', prop_name, value))

    def url(self, prop_name: str, value: str):
        return self.caller.stash(WriteSimplePageProperty.url(prop_name, value))

    def email(self, prop_name: str, value: str):
        return self.caller.stash(WriteSimplePageProperty.email(prop_name, value))

    def phone_number(self, prop_name: str, value: str):
        return self.caller.stash(WriteSimplePageProperty.phone_number(prop_name, value))

    def date(self, prop_name: str, start_date: Union[datetimeclass, dateclass], end_date=None):
        return self.caller.stash(WriteSimplePageProperty.date(prop_name, start_date, end_date))

    def number(self, prop_name: str, value: Union[int, float]):
        return self.caller.stash(WriteSimplePageProperty.number(prop_name, value))

    def checkbox(self, prop_name: str, value: bool):
        return self.caller.stash(WriteSimplePageProperty.checkbox(prop_name, value))

    def select(self, prop_name: str, value: str):
        return self.caller.stash(WriteSimplePageProperty.select(prop_name, value))

    def files(self, prop_name: str, value: str):
        return self.caller.stash(WriteSimplePageProperty.files(prop_name, value))

    def people(self, prop_name: str, value: str):
        return self.caller.stash(WriteSimplePageProperty.people(prop_name, value))

    def multi_select(self, prop_name: str, values: list[str]):
        return self.caller.stash(WriteSimplePageProperty.multi_select(prop_name, values))

    def relation(self, prop_name: str, page_ids: list[str]):
        return self.caller.stash(WriteSimplePageProperty.relation(prop_name, page_ids))
