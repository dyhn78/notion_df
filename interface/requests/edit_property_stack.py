from interface.requests.edit_property_unit import *
from interface.requests.structures import DictStash, ListStash


class PagePropertyStack(DictStash):
    def apply(self):
        return {'properties': self.stash()}

    def add_title(self, prop_name: str):
        carrier = RichTextProperty(prop_name, 'title')
        return self.add_to_dictstash(carrier)


class DatabasePropertyStack(PagePropertyStack):
    def add_number(self, prop_name: str, prop_value):
        carrier = RelationProperty(prop_name, prop_value)
        return self.add_to_dictstash(carrier)

    def add_checkbox(self, prop_name: str, prop_value):
        carrier = RelationProperty(prop_name, prop_value)
        return self.add_to_dictstash(carrier)

    def add_select(self, prop_name: str, prop_value):
        carrier = RelationProperty(prop_name, prop_value)
        return self.add_to_dictstash(carrier)

    def add_files(self, prop_name: str, prop_value):
        carrier = FilesProperty(prop_name, prop_value)
        return self.add_to_dictstash(carrier)

    def add_people(self, prop_name: str, prop_value):
        carrier = PeopleProperty(prop_name, prop_value)
        return self.add_to_dictstash(carrier)

    def add_multi_select(self, prop_name: str, prop_values: list[str]):
        carrier = MultiSelectProperty(prop_name, prop_values)
        return self.add_to_dictstash(carrier)

    def add_relation(self, prop_name: str, prop_values: list[str]):
        carrier = RelationProperty(prop_name, prop_values)
        return self.add_to_dictstash(carrier)

    def add_date(self, prop_name: str, start_date: str, end_date: str):
        carrier = DateProperty(prop_name, start_date, end_date)
        return self.add_to_dictstash(carrier)

    def add_rich_text(self, prop_name: str):
        carrier = RichTextProperty(prop_name, 'rich_text')
        return self.add_to_dictstash(carrier)


class BlockChildrenStack(ListStash):
    def apply(self):
        return {'children': self.stash()}

    def append_page(self, title):
        carrier = PlainCarrier({'title': title})
        carrier = make_block_type(carrier.apply, 'child_page')
        return self.append_to_liststash(carrier)

    def append_paragraph(self):
        carrier = RichTextProperty('text', 'text', 'paragraph')
        return self.append_to_liststash(carrier)

    def append_heading_1(self):
        carrier = RichTextProperty('text', 'text', 'heading_1')
        return self.append_to_liststash(carrier)

    def append_heading_2(self):
        carrier = RichTextProperty('text', 'text', 'heading_2')
        return self.append_to_liststash(carrier)

    def append_heading_3(self):
        carrier = RichTextProperty('text', 'text', 'heading_3')
        return self.append_to_liststash(carrier)

    def append_bulleted_list(self):
        carrier = RichTextProperty('text', 'text', 'bulleted_list_item')
        return self.append_to_liststash(carrier)

    def append_numbered_list(self):
        carrier = RichTextProperty('text', 'text', 'numbered_list_item')
        return self.append_to_liststash(carrier)

    def append_to_do(self, checked=False):
        carrier = RichTextProperty('text', 'text', 'to_do')
        return self.append_to_liststash(carrier)

    def append_toggle(self):
        carrier = RichTextProperty('text', 'text', 'toggle')
        return self.append_to_liststash(carrier)
