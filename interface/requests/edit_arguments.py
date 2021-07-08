from typing import Union
from datetime import datetime as datetimeclass, date as dateclass

from interface.requests.edit_blocks import TextBlock, PageBlock
from interface.requests.edit_property_unit import PageProperty, RichTextProperty
from interface.structure.carriers import TwofoldDictStash, TwofoldListStash


class PagePropertyStack(TwofoldDictStash):
    def apply(self):
        return {'properties': self._unpack()}

    def add_title(self, prop_name: str):
        self.stash(RichTextProperty(prop_name, 'title'))


class DatabasePropertyStack(PagePropertyStack):
    def write_rich_text(self, prop_name: str):
        self.stash(RichTextProperty(prop_name, 'rich_text'))

    def write_number(self, prop_name: str, value):
        self.stash(PageProperty.number(prop_name, value))

    def write_checkbox(self, prop_name: str, value):
        self.stash(PageProperty.checkbox(prop_name, value))

    def write_select(self, prop_name: str, value):
        self.stash(PageProperty.select(prop_name, value))

    def write_files(self, prop_name: str, value):
        self.stash(PageProperty.files(prop_name, value))

    def write_people(self, prop_name: str, value):
        self.stash(PageProperty.people(prop_name, value))

    def write_multi_select(self, prop_name: str, values: list[str]):
        self.stash(PageProperty.multi_select(prop_name, values))

    def write_relation(self, prop_name: str, page_ids: list[str]):
        self.stash(PageProperty.relation(prop_name, page_ids))

    def write_date(self, prop_name: str, start_date: Union[datetimeclass, dateclass], end_date=None):
        self.stash(PageProperty.date(prop_name, start_date, end_date))


class BlockChildrenStack(TwofoldListStash):
    def apply(self):
        return {'children': self._unpack()}

    def write(self):
        return BlockChildAgent(self)

    def write_plain(self):
        return PlainBlockChildAgent(self)


class BlockChildAgent:
    def __init__(self, caller: BlockChildrenStack):
        self.caller = caller

    def page(self, title):
        return self.caller.stash(PageBlock(title))

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
