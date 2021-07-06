from interface.requests.edit_blocks import TextBlock, PageBlock, PlainTextBlock
from interface.requests.edit_property_unit import *
from interface.structure.carriers import TwofoldDictStash, TwofoldListStash


class PagePropertyStack(TwofoldDictStash):
    def apply(self):
        return {'properties': self._unpack()}

    def add_title(self, prop_name: str):
        carrier = RichTextProperty(prop_name, 'title')
        return self.stash(carrier)


class DatabasePropertyStack(PagePropertyStack):
    def add_number(self, prop_name: str, prop_value):
        carrier = NumberProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_checkbox(self, prop_name: str, prop_value):
        carrier = CheckboxProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_select(self, prop_name: str, prop_value):
        carrier = SelectProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_files(self, prop_name: str, prop_value):
        carrier = FilesProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_people(self, prop_name: str, prop_value):
        carrier = PeopleProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_multi_select(self, prop_name: str, prop_values: list[str]):
        carrier = MultiSelectProperty(prop_name, prop_values)
        return self.stash(carrier)

    def add_relation(self, prop_name: str, prop_values: list[str]):
        carrier = RelationProperty(prop_name, prop_values)
        return self.stash(carrier)

    def add_date(self, prop_name: str, start_date: Union[datetimeclass, dateclass], end_date=None):
        carrier = DateProperty(prop_name, start_date, end_date)
        return self.stash(carrier)

    def add_rich_text(self, prop_name: str):
        carrier = RichTextProperty(prop_name, 'rich_text')
        return self.stash(carrier)


class BlockChildrenStack(TwofoldListStash):
    def apply(self):
        return {'children': self._unpack()}

    def add_page(self, title):
        return self.stash(PageBlock(title))

    def add_paragraph(self):
        return self.stash(TextBlock('paragraph'))

    def add_heading_1(self):
        return self.stash(TextBlock('heading_1'))

    def add_heading_2(self):
        return self.stash(TextBlock('heading_2'))

    def add_heading_3(self):
        return self.stash(TextBlock('heading_3'))

    def add_bulleted_list(self):
        return self.stash(TextBlock('bulleted_list_item'))

    def add_numbered_list(self):
        return self.stash(TextBlock('numbered_list_item'))

    def add_to_do(self, checked=False):
        return self.stash(TextBlock('to_do', checked=checked))

    def add_toggle(self):
        return self.stash(TextBlock('toggle'))

    def add_plain_paragraph(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'paragraph'))

    def add_plain_heading_1(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'heading_1'))

    def add_plain_heading_2(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'heading_2'))

    def add_plain_heading_3(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'heading_3'))

    def add_plain_bulleted_list(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'bulleted_list_item'))

    def add_plain_numbered_list(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'numbered_list_item'))

    def add_plain_to_do(self, text_content, checked=False):
        return self.stash(PlainTextBlock(text_content, checked=checked))

    def add_plain_toggle(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'toggle'))
