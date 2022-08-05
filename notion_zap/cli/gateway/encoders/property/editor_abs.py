from abc import abstractmethod, ABCMeta
from datetime import datetime, date
from typing import Union, Optional, Any, Hashable

from notion_zap.cli.core import PropertyFrame, DatePropertyValue
from .carrier import (
    PropertyEncoder, RichTextPropertyEncoder,
    SimplePropertyEncoder, FilesPropertyEncoder)


class PageRowPropertyWriter(metaclass=ABCMeta):
    def __init__(self, frame: PropertyFrame):
        self.frame = frame

    @abstractmethod
    def push_encoder(self, prop_key: str, encoder: PropertyEncoder):
        pass

    def clean_key(self, key: str, key_alias: Hashable) -> str:
        assert bool(key) + bool(key_alias) == 1
        if key:
            return key
        else:
            return self.frame.get_key(key_alias)

    def clean_value(self, key: str, value: Any, value_alias: Hashable):
        column = self.frame.by_key[key]
        assert bool(value is not None) + bool(value_alias is not None) <= 1
        if value is not None:
            return value
        elif value_alias is not None:
            try:
                return column.marks[value_alias].value
            except KeyError:
                raise KeyError(f"{value_alias=}, {column.marks.keys=}")
        return None

    def clean_values(self, key: str, value: Any, value_aliases: Optional[list[Hashable]]):
        column = self.frame.by_key[key]
        assert bool(value is not None) + bool(value_aliases is not None) <= 1
        if value is not None:
            return value
        else:
            try:
                return [column.marks[label].value for label in value_aliases]
            except KeyError:
                raise KeyError(f"{value_aliases=}, {column.marks.keys=}")

    def write_rich(self, key: str = None, key_alias: Hashable = None, data_type=''):
        key = self.clean_key(key, key_alias)
        if not data_type:
            data_type = self.frame.get_type(key)
        try:
            func = getattr(self, f'write_rich_{data_type}')
        except AttributeError:
            raise ValueError(
                f'data_types should be one of {self.valid_data_types__write_rich()};'
                f'your input: {data_type=}')
        return func(key=key)

    @classmethod
    def valid_data_types__write_rich(cls):
        return [func_name for func_name in dir(cls)
                if func_name.startswith('write_rich_')]

    def write_rich_text(self, key: str = None, key_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        encoder = RichTextPropertyEncoder(key, 'rich_text')
        return self.push_encoder(key, encoder)

    def write_rich_title(self, key: str = None, key_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        encoder = RichTextPropertyEncoder(key, 'title')
        return self.push_encoder(key, encoder)

    def write(
            self, key: str = None, key_alias: Hashable = None, data_type='',
            value: Any = None,
            value_aliases: Optional[list[Hashable]] = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_values(key, value, value_aliases)
        if not data_type:
            data_type = self.frame.get_type(key)
        try:
            func = getattr(self, f'write_{data_type}')
        except AttributeError:
            raise ValueError(
                f'data_types should be one of {self.valid_data_types__write()};'
                f'your input: {data_type=}')
        return func(key=key, value=value)

    @classmethod
    def valid_data_types__write(cls):
        return [func_name for func_name in dir(cls)
                if func_name.startswith('write_') and
                not func_name.startswith('write_rich_')]

    def write_text(
            self, key: str = None, key_alias: Hashable = None, value: str = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = self.write_rich_text(key=key)
        encoder.write_text(value)
        return encoder

    def write_title(
            self, key: str = None, key_alias: Hashable = None, value: str = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = self.write_rich_title(key=key)
        encoder.write_text(value)
        return encoder

    def write_multi_select(
            self, key: str = None, key_alias: Hashable = None,
            value: list[str] = None,
            value_aliases: Optional[list[Hashable]] = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_values(key, value, value_aliases)
        encoder = SimplePropertyEncoder.multi_select(key, value)
        return self.push_encoder(key, encoder)

    def write_relation(
            self, key: str = None, key_alias: Hashable = None,
            value: list[str] = None,
            value_aliases: Optional[list[Hashable]] = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_values(key, value, value_aliases)
        encoder = SimplePropertyEncoder.relation(key, value)
        return self.push_encoder(key, encoder)

    def write_people(
            self, key: str = None, key_alias: Hashable = None,
            value: Any = None,
            value_aliases: Optional[list[Hashable]] = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_values(key, value, value_aliases)
        encoder = SimplePropertyEncoder.people(key, value)
        return self.push_encoder(key, encoder)

    def write_files(self, key: str = None, key_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        encoder = FilesPropertyEncoder(key)
        return self.push_encoder(key, encoder)

    def write_date(
            self, key: str = None, key_alias: Hashable = None,
            value: Union[DatePropertyValue, datetime, date] = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        value = DatePropertyValue.from_date(value)
        encoder = SimplePropertyEncoder.date(key, value)
        return self.push_encoder(key, encoder)

    def write_select(
            self, key: str = None, key_alias: Hashable = None, value: str = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = SimplePropertyEncoder.select(key, value)
        return self.push_encoder(key, encoder)

    def write_checkbox(
            self, key: str = None, key_alias: Hashable = None, value: bool = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = SimplePropertyEncoder.checkbox(key, value)
        return self.push_encoder(key, encoder)

    def write_number(
            self, key: str = None, key_alias: Hashable = None, value: Union[int, float] = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = SimplePropertyEncoder.number(key, value)
        return self.push_encoder(key, encoder)

    def write_phone_number(
            self, key: str = None, key_alias: Hashable = None, value: str = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = SimplePropertyEncoder.phone_number(key, value)
        return self.push_encoder(key, encoder)

    def write_email(
            self, key: str = None, key_alias: Hashable = None, value: str = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = SimplePropertyEncoder.email(key, value)
        return self.push_encoder(key, encoder)

    def write_url(
            self, key: str = None, key_alias: Hashable = None, value: str = None,
            value_alias: Hashable = None):
        key = self.clean_key(key, key_alias)
        value = self.clean_value(key, value, value_alias)
        encoder = SimplePropertyEncoder.url(key, value)
        return self.push_encoder(key, encoder)
