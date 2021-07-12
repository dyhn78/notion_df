from collections import defaultdict
from typing import Union
from datetime import datetime as datetimeclass, date as dateclass

from .blocks import TextBlock, Block
from .property_unit import PageProperty, RichTextProperty
from notion_py.interface.structure import TwofoldDictStash, TwofoldListStash


class PagePropertyStack(TwofoldDictStash):
    def __init__(self):
        super().__init__()
        self.read = defaultdict(dict)

    def apply(self):
        return {'properties': self._unpack()}

    @property
    def write(self):
        return PagePropertyAgent(self)

    @property
    def write_plain(self):
        return PlainPagePropertyAgent(self)


class PagePropertyAgent:
    def __init__(self, caller: PagePropertyStack):
        self.caller = caller

    def title(self, prop_name: str):
        self.caller.stash(RichTextProperty('title', prop_name))


class PlainPagePropertyAgent:
    def __init__(self, caller: PagePropertyStack):
        self.caller = caller

    def title(self, prop_name: str, value):
        self.caller.stash(RichTextProperty.plain_form('title', prop_name, value))


class DatabasePropertyStack(PagePropertyStack):
    @property
    def write(self):
        return DatabasePropertyAgent(self)

    @property
    def write_plain(self):
        return PlainDatabasePropertyAgent(self)


class PlainDatabasePropertyAgent(PlainPagePropertyAgent):
    def text(self, prop_name: str, value):
        self.caller.stash(RichTextProperty.plain_form('rich_text', prop_name, value))


class DatabasePropertyAgent(PagePropertyAgent):
    def text(self, prop_name: str):
        self.caller.stash(RichTextProperty('rich_text', prop_name))

    def date(self, prop_name: str, start_date: Union[datetimeclass, dateclass], end_date=None):
        self.caller.stash(PageProperty.date(prop_name, start_date, end_date))

    def number(self, prop_name: str, value):
        self.caller.stash(PageProperty.number(prop_name, value))

    def checkbox(self, prop_name: str, value):
        self.caller.stash(PageProperty.checkbox(prop_name, value))

    def select(self, prop_name: str, value):
        self.caller.stash(PageProperty.select(prop_name, value))

    def files(self, prop_name: str, value):
        self.caller.stash(PageProperty.files(prop_name, value))

    def people(self, prop_name: str, value):
        self.caller.stash(PageProperty.people(prop_name, value))

    def multi_select(self, prop_name: str, values: list[str]):
        self.caller.stash(PageProperty.multi_select(prop_name, values))

    def relation(self, prop_name: str, page_ids: list[str]):
        self.caller.stash(PageProperty.relation(prop_name, page_ids))


class BlockChildrenStack(TwofoldListStash):
    def apply(self):
        return {'children': self._unpack()}

    def write(self):
        return BlockChildAgent(self)

    def write_plain(self):
        return PlainBlockChildAgent(self)


class PlainBlockChildAgent:
    def __init__(self, caller: BlockChildrenStack):
        self.caller = caller

    def paragraph(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'paragraph'))

    def heading_1(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'heading_1'))

    def heading_2(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'heading_2'))

    def heading_3(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'heading_3'))

    def bulleted_list(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'bulleted_list_item'))

    def numbered_list(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'numbered_list_item'))

    def to_do(self, text_content, checked=False):
        return self.caller.stash(TextBlock.plain_form(text_content, 'to_do', checked=checked))

    def toggle(self, text_content):
        return self.caller.stash(TextBlock.plain_form(text_content, 'toggle'))


class BlockChildAgent:
    def __init__(self, caller: BlockChildrenStack):
        self.caller = caller

    def page(self, title):
        return self.caller.stash(Block.page(title))

    def paragraph(self):
        return self.caller.stash(TextBlock('paragraph'))

    def heading_1(self):
        return self.caller.stash(TextBlock('heading_1'))

    def heading_2(self):
        return self.caller.stash(TextBlock('heading_2'))

    def heading_3(self):
        return self.caller.stash(TextBlock('heading_3'))

    def bulleted_list(self):
        return self.caller.stash(TextBlock('bulleted_list_item'))

    def numbered_list(self):
        return self.caller.stash(TextBlock('numbered_list_item'))

    def to_do(self, checked=False):
        return self.caller.stash(TextBlock('to_do', checked=checked))

    def toggle(self):
        return self.caller.stash(TextBlock('toggle'))
