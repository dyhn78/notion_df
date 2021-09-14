from abc import ABC, abstractmethod, ABCMeta
from typing import Union

from notion_py.interface.struct import DateFormat
from .maker import \
    PropertyEncoder, RichTextPropertyEncoder, SimplePropertyEncoder


class TabularPropertybyName(ABC):
    @abstractmethod
    def _type_of(self, prop_name: str):
        pass

    @abstractmethod
    def push_carrier(self, prop_name: str, carrier: PropertyEncoder):
        pass

    def write(self, prop_name: str, prop_value, prop_type=''):
        if not prop_type:
            prop_type = self._type_of(prop_name)
        writer_func = f'write_{prop_type}'
        return getattr(self, writer_func)(prop_name, prop_value)

    def write_rich(self, prop_name: str, prop_type=''):
        if not prop_type:
            prop_type = self._type_of(prop_name)
        writer_func = f'write_rich_{prop_type}'
        return getattr(self, writer_func)(prop_name)

    def write_rich_text(self, prop_name: str) -> RichTextPropertyEncoder:
        writer = RichTextPropertyEncoder('rich_text', prop_name)
        return self.push_carrier(prop_name, writer)

    def write_text(self, prop_name: str, value: str):
        writer = self.write_rich_text(prop_name)
        writer.write_text(value)
        return writer

    def write_rich_title(self, prop_name: str) -> RichTextPropertyEncoder:
        writer = RichTextPropertyEncoder('title', prop_name)
        return self.push_carrier(prop_name, writer)

    def write_title(self, prop_name: str, value: str):
        writer = self.write_rich_title(prop_name)
        writer.write_text(value)
        return writer

    def write_date(self, prop_name: str, value: DateFormat):
        return self.push_carrier(prop_name, SimplePropertyEncoder.date(prop_name, value))

    def write_url(self, prop_name: str, value: str):
        return self.push_carrier(prop_name, SimplePropertyEncoder.url(prop_name, value))

    def write_email(self, prop_name: str, value: str):
        return self.push_carrier(prop_name, SimplePropertyEncoder.email(prop_name, value))

    def write_phone_number(self, prop_name: str, value: str):
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.phone_number(prop_name, value))

    def write_number(self, prop_name: str, value: Union[int, float]):
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.number(prop_name, value))

    def write_checkbox(self, prop_name: str, value: bool):
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.checkbox(prop_name, value))

    def write_select(self, prop_name: str, value: str):
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.select(prop_name, value))

    def write_files(self, prop_name: str, value: str):
        return self.push_carrier(prop_name, SimplePropertyEncoder.files(prop_name, value))

    def write_people(self, prop_name: str, value: str):
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.people(prop_name, value))

    def write_multi_select(self, prop_name: str, values: Union[list[str], str]):
        if isinstance(values, str):
            values = [values]
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.multi_select(prop_name, values))

    def write_relation(self, prop_name: str, values: Union[list[str], str]):
        """ values: list of <page_id>"""
        if isinstance(values, str):
            values = [values]
        return self.push_carrier(prop_name,
                                 SimplePropertyEncoder.relation(prop_name, values))


class TabularPropertybyKey(TabularPropertybyName, metaclass=ABCMeta):
    @abstractmethod
    def _name_at(self, prop_key: str):
        pass

    def write_at(self, prop_key: str, prop_value, prop_type=''):
        prop_name = self._name_at(prop_key)
        return self.write(prop_name, prop_value, prop_type)

    def write_rich_at(self, prop_key: str, prop_type=''):
        prop_name = self._name_at(prop_key)
        return self.write_rich(prop_name, prop_type)

    def write_rich_title_at(self, prop_key: str):
        prop_name = self._name_at(prop_key)
        return self.write_rich_title(prop_name)

    def write_rich_text_at(self, prop_key: str):
        prop_name = self._name_at(prop_key)
        return self.write_rich_text(prop_name)

    def write_title_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_title(prop_name, value)

    def write_text_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_text(prop_name, value)

    def write_date_at(self, prop_key: str, value: DateFormat):
        prop_name = self._name_at(prop_key)
        return self.write_date(prop_name, value)

    def write_url_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_url(prop_name, value)

    def write_email_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_email(prop_name, value)

    def write_phone_number_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_phone_number(prop_name, value)

    def write_number_at(self, prop_key: str, value: Union[int, float]):
        prop_name = self._name_at(prop_key)
        return self.write_number(prop_name, value)

    def write_checkbox_at(self, prop_key: str, value: bool):
        prop_name = self._name_at(prop_key)
        return self.write_checkbox(prop_name, value)

    def write_select_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_select(prop_name, value)

    def write_files_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_files(prop_name, value)

    def write_people_at(self, prop_key: str, value: str):
        prop_name = self._name_at(prop_key)
        return self.write_people(prop_name, value)

    def write_multi_select_at(self, prop_key: str, values: Union[list[str], str]):
        prop_name = self._name_at(prop_key)
        return self.write_multi_select(prop_name, values)

    def write_relation_at(self, prop_key: str, values: Union[list[str], str]):
        prop_name = self._name_at(prop_key)
        return self.write_relation(prop_name, values)