from interface.requests.edit_blocks import TextBlock, TitleBlock, TodoBlock, PlainTextBlock, PlainTodoBlock
from interface.requests.edit_property_unit import *
from interface.requests.structures import TwofoldDictStash, TwofoldListStash


class PagePropertyStack(TwofoldDictStash):
    def apply(self):
        return {'properties': self._unpack()}

    def add_title(self, prop_name: str):
        carrier = RichTextProperty(prop_name, 'title')
        return self.stash(carrier)


class DatabasePropertyStack(PagePropertyStack):
    def add_number(self, prop_name: str, prop_value):
        carrier = RelationProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_checkbox(self, prop_name: str, prop_value):
        carrier = RelationProperty(prop_name, prop_value)
        return self.stash(carrier)

    def add_select(self, prop_name: str, prop_value):
        carrier = RelationProperty(prop_name, prop_value)
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

    def append_page(self, title):
        return self.stash(TitleBlock(title))

    def append_paragraph(self):
        return self.stash(TextBlock('paragraph'))

    def append_heading_1(self):
        return self.stash(TextBlock('heading_1'))

    def append_heading_2(self):
        return self.stash(TextBlock('heading_2'))

    def append_heading_3(self):
        return self.stash(TextBlock('heading_3'))

    def append_bulleted_list(self):
        return self.stash(TextBlock('bulleted_list_item'))

    def append_numbered_list(self):
        return self.stash(TextBlock('numbered_list_item'))

    def append_to_do(self, checked=False):
        return self.stash(TodoBlock(checked))

    def append_toggle(self):
        return self.stash(TextBlock('toggle'))

    def append_plain_paragraph(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'paragraph'))

    def append_plain_heading_1(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'heading_1'))

    def append_plain_heading_2(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'heading_2'))

    def append_plain_heading_3(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'heading_3'))

    def append_plain_bulleted_list(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'bulleted_list_item'))

    def append_plain_numbered_list(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'numbered_list_item'))

    def append_plain_to_do(self, text_content, checked=False):
        return self.stash(PlainTodoBlock(text_content, checked))

    def append_plain_toggle(self, text_content):
        return self.stash(PlainTextBlock(text_content, 'toggle'))
