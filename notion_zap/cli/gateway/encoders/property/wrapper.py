from abc import ABC, abstractmethod, ABCMeta
from datetime import datetime, date
from typing import Union

from notion_zap.cli.struct import DateFormat
from .maker import (
    PropertyEncoder, RichTextPropertyEncoder,
    SimplePropertyEncoder, FilesPropertyEncoder)


class PageRowPropertybyName(ABC):
    @abstractmethod
    def _type_of(self, prop_key: str):
        pass

    @abstractmethod
    def push_carrier(self, prop_key: str, carrier: PropertyEncoder):
        pass

    def write_rich(self, prop_key: str, prop_type=''):
        if not prop_type:
            prop_type = self._type_of(prop_key)
        writer_func = f'write_rich_{prop_type}'
        return getattr(self, writer_func)(prop_key)

    def write(self, prop_key: str, prop_value, prop_type=''):
        if not prop_type:
            prop_type = self._type_of(prop_key)
        writer_func = f'write_{prop_type}'
        return getattr(self, writer_func)(prop_key, prop_value)

    def write_rich_text(self, prop_key: str) -> RichTextPropertyEncoder:
        writer = RichTextPropertyEncoder(prop_key, 'rich_text')
        return self.push_carrier(prop_key, writer)

    def write_rich_title(self, prop_key: str) -> RichTextPropertyEncoder:
        writer = RichTextPropertyEncoder(prop_key, 'title')
        return self.push_carrier(prop_key, writer)

    def write_files(self, prop_key: str) -> FilesPropertyEncoder:
        writer = FilesPropertyEncoder(prop_key)
        return self.push_carrier(prop_key, writer)

    def write_text(self, prop_key: str, value: str):
        writer = self.write_rich_text(prop_key)
        writer.write_text(value)
        return writer

    def write_title(self, prop_key: str, value: str):
        writer = self.write_rich_title(prop_key)
        writer.write_text(value)
        return writer

    def write_date(self, prop_key: str, value: Union[DateFormat, datetime, date]):
        cleaned_value = DateFormat.from_date_val(value)
        carrier = SimplePropertyEncoder.date(prop_key, cleaned_value)
        return self.push_carrier(prop_key, carrier)

    def write_url(self, prop_key: str, value: str):
        return self.push_carrier(prop_key, SimplePropertyEncoder.url(prop_key, value))

    def write_email(self, prop_key: str, value: str):
        return self.push_carrier(prop_key, SimplePropertyEncoder.email(prop_key, value))

    def write_phone_number(self, prop_key: str, value: str):
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.phone_number(prop_key, value))

    def write_number(self, prop_key: str, value: Union[int, float]):
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.number(prop_key, value))

    def write_checkbox(self, prop_key: str, value: bool):
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.checkbox(prop_key, value))

    def write_select(self, prop_key: str, value: str):
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.select(prop_key, value))

    def write_people(self, prop_key: str, value: str):
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.people(prop_key, value))

    def write_multi_select(self, prop_key: str, values: Union[list[str], str]):
        if isinstance(values, str):
            values = [values]
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.multi_select(prop_key, values))

    def write_relation(self, prop_key: str, values: Union[list[str], str]):
        """ blocks: list of <page_id>"""
        if isinstance(values, str):
            values = [values]
        return self.push_carrier(prop_key,
                                 SimplePropertyEncoder.relation(prop_key, values))


class PageRowPropertybyKey(PageRowPropertybyName, metaclass=ABCMeta):
    @abstractmethod
    def _name_at(self, prop_tag: str):
        pass

    def write_at(self, prop_tag: str, prop_value, prop_type=''):
        prop_key = self._name_at(prop_tag)
        return self.write(prop_key, prop_value, prop_type)

    def write_rich_at(self, prop_tag: str, prop_type=''):
        prop_key = self._name_at(prop_tag)
        return self.write_rich(prop_key, prop_type)

    def write_rich_title_at(self, prop_tag: str):
        prop_key = self._name_at(prop_tag)
        return self.write_rich_title(prop_key)

    def write_rich_text_at(self, prop_tag: str):
        prop_key = self._name_at(prop_tag)
        return self.write_rich_text(prop_key)

    def write_files_at(self, prop_tag: str):
        prop_key = self._name_at(prop_tag)
        return self.write_files(prop_key)

    def write_title_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_title(prop_key, value)

    def write_text_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_text(prop_key, value)

    def write_date_at(self, prop_tag: str, value: Union[DateFormat, datetime, date]):
        prop_key = self._name_at(prop_tag)
        return self.write_date(prop_key, value)

    def write_url_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_url(prop_key, value)

    def write_email_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_email(prop_key, value)

    def write_phone_number_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_phone_number(prop_key, value)

    def write_number_at(self, prop_tag: str, value: Union[int, float]):
        prop_key = self._name_at(prop_tag)
        return self.write_number(prop_key, value)

    def write_checkbox_at(self, prop_tag: str, value: bool):
        prop_key = self._name_at(prop_tag)
        return self.write_checkbox(prop_key, value)

    def write_select_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_select(prop_key, value)

    def write_people_at(self, prop_tag: str, value: str):
        prop_key = self._name_at(prop_tag)
        return self.write_people(prop_key, value)

    def write_multi_select_at(self, prop_tag: str, values: Union[list[str], str]):
        prop_key = self._name_at(prop_tag)
        return self.write_multi_select(prop_key, values)

    def write_relation_at(self, prop_tag: str, values: Union[list[str], str]):
        prop_key = self._name_at(prop_tag)
        return self.write_relation(prop_key, values)
