from edit__property import *
from interface.requests.structures import DictStash, ListStash


class PagePropertyStack(DictStash):
    def apply(self):
        return {'properties': self.stash()}

    def add_title(self, prop_name):
        handler = RichTextCarrier(prop_name, 'title')
        return self.edit(handler)


class DatabasePropertyStack(PagePropertyStack):
    def add_rich_text(self, prop_name):
        handler = RichTextCarrier(prop_name, 'rich_text')
        return self.edit(handler)

    def add_date(self, prop_name, start_date, end_date):
        handler = DateCarrier(prop_name, start_date, end_date)
        return self.edit(handler)

    def add_multi_select(self, prop_name, prop_values):
        handler = MultiSelectProperty(prop_name, prop_values)
        return self.edit(handler)

    def add_relation(self, prop_name, prop_value):
        handler = RelationProperty(prop_name, prop_value)
        return self.edit(handler)

    def add_number(self, prop_name, prop_value):
        handler = RelationProperty(prop_name, prop_value)
        return self.edit(handler)

    def add_checkbox(self, prop_name, prop_value):
        handler = RelationProperty(prop_name, prop_value)
        return self.edit(handler)

    def add_select(self, prop_name, prop_value):
        handler = RelationProperty(prop_name, prop_value)
        return self.edit(handler)

    def add_files(self, prop_name, prop_value):
        handler = FilesProperty(prop_name, prop_value)
        return self.edit(handler)

    def add_people(self, prop_name, prop_value):
        handler = PeopleProperty(prop_name, prop_value)
        return self.edit(handler)


class BlockChildrenStack(ListStash):
    def apply(self):
        return {'children': self.stash()}

    def append_page(self, title):
        handler = PlainCarrier({'title': title})
        handler = make_block_type(handler.apply, 'child_page')
        return self.append(handler)

    def append_paragraph(self):
        handler = RichTextCarrier('text', 'text', 'paragraph')
        return self.append(handler)

    def append_heading_1(self):
        handler = RichTextCarrier('text', 'text', 'heading_1')
        return self.append(handler)

    def append_heading_2(self):
        handler = RichTextCarrier('text', 'text', 'heading_2')
        return self.append(handler)

    def append_heading_3(self):
        handler = RichTextCarrier('text', 'text', 'heading_3')
        return self.append(handler)

    def append_bulleted_list(self):
        handler = RichTextCarrier('text', 'text', 'bulleted_list_item')
        return self.append(handler)

    def append_numbered_list(self):
        handler = RichTextCarrier('text', 'text', 'numbered_list_item')
        return self.append(handler)

    def append_to_do(self, checked=False):
        handler = RichTextCarrier('text', 'text', 'to_do')
        return self.append(handler)

    def append_toggle(self):
        handler = RichTextCarrier('text', 'text', 'toggle')
        return self.append(handler)
