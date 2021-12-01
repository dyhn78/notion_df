from abc import abstractmethod, ABCMeta
from datetime import datetime, date
from typing import Union, Optional, Any, Hashable

from notion_zap.cli.structs import DateObject, PropertyFrame
from .carrier import (
    PropertyEncoder, RichTextPropertyEncoder,
    SimplePropertyEncoder, FilesPropertyEncoder)


class PageRowPropertyWriter(metaclass=ABCMeta):
    def __init__(self, frame: PropertyFrame):
        self.frame = frame

    @abstractmethod
    def push_encoder(self, prop_key: str, encoder: PropertyEncoder):
        pass

    def _cleaned_key(self, key: str, tag: Hashable) -> str:
        assert bool(key) + bool(tag) == 1
        if key:
            cleaned_key = key
        else:
            cleaned_key = self.frame.key_of(tag)
        return cleaned_key

    def _cleaned_key_with_a_value(
            self, key: str, tag: Hashable, value: Any, label: Hashable):
        cleaned_key = self._cleaned_key(key, tag)
        column = self.frame.by_key[cleaned_key]
        assert bool(value is not None) + bool(label is not None) == 1
        if value:
            cleaned_value = value
        else:
            cleaned_value = column.labels[label]
        return cleaned_key, cleaned_value

    def _cleaned_key_with_value_list(
            self, key: str, tag: Hashable, value: Any,
            label: Hashable, label_list: list[Hashable],
            mark: Hashable) -> tuple[str, Any]:
        cleaned_key = self._cleaned_key(key, tag)
        column = self.frame.by_key[cleaned_key]
        assert sum(arg is not None
                   for arg in [value, label, label_list, mark]) == 1
        if value:
            cleaned_value = value
        elif label:
            cleaned_value = column.labels[label]
        elif label_list:
            cleaned_value = [column.labels[label] for label in label_list]
        else:
            cleaned_value = column.marks[mark]
        return cleaned_key, cleaned_value

    def write_rich(self, key: str = None, tag: Hashable = None, data_type=''):
        key = self._cleaned_key(key, tag)
        if not data_type:
            data_type = self.frame.type_of(key)
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

    def write_rich_text(self, key: str = None, tag: Hashable = None):
        key = self._cleaned_key(key, tag)
        encoder = RichTextPropertyEncoder(key, 'rich_text')
        return self.push_encoder(key, encoder)

    def write_rich_title(self, key: str = None, tag: Hashable = None):
        key = self._cleaned_key(key, tag)
        encoder = RichTextPropertyEncoder(key, 'title')
        return self.push_encoder(key, encoder)

    def write(
            self, key: str = None, tag: Hashable = None, data_type='',
            value: Any = None,
            label: Hashable = None,
            label_list: Optional[list[Hashable]] = None, mark: Hashable = None):
        key, value = self._cleaned_key_with_value_list(key, tag, value, label, label_list,
                                                       mark)
        if not data_type:
            data_type = self.frame.type_of(key)
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
            self, key: str = None, tag: Hashable = None, value: str = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = self.write_rich_text(key=key)
        encoder.write_text(value)
        return encoder

    def write_title(
            self, key: str = None, tag: Hashable = None, value: str = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = self.write_rich_title(key=key)
        encoder.write_text(value)
        return encoder

    def write_multi_select(
            self, key: str = None, tag: Hashable = None,
            value: str = None,
            label: Hashable = None,
            label_list: Optional[list[Hashable]] = None, mark: Hashable = None):
        key, value = self._cleaned_key_with_value_list(key, tag, value, label, label_list,
                                                       mark)
        if isinstance(value, str):
            cleaned_value = [value]
        elif isinstance(value, list):
            cleaned_value = value
        else:
            raise ValueError(value)
        encoder = SimplePropertyEncoder.multi_select(key, cleaned_value)
        return self.push_encoder(key, encoder)

    def write_relation(
            self, key: str = None, tag: Hashable = None,
            value: str = None,
            label: Hashable = None,
            label_list: Optional[list[Hashable]] = None, mark: Hashable = None):
        key, value = self._cleaned_key_with_value_list(key, tag, value, label, label_list,
                                                       mark)
        if isinstance(value, str):
            cleaned_value = [value]
        elif isinstance(value, list):
            cleaned_value = value
        else:
            raise ValueError(value)
        encoder = SimplePropertyEncoder.relation(key, cleaned_value)
        return self.push_encoder(key, encoder)

    def write_people(
            self, key: str = None, tag: Hashable = None,
            value: Any = None,
            label: Hashable = None,
            label_list: Optional[list[Hashable]] = None, mark: Hashable = None):
        key, value = self._cleaned_key_with_value_list(key, tag, value, label, label_list,
                                                       mark)
        if isinstance(value, str):
            cleaned_value = [value]
        elif isinstance(value, list):
            cleaned_value = value
        else:
            raise ValueError(value)
        encoder = SimplePropertyEncoder.people(key, cleaned_value)
        return self.push_encoder(key, encoder)

    def write_files(self, key: str = None, tag: Hashable = None):
        key = self._cleaned_key(key, tag)
        encoder = FilesPropertyEncoder(key)
        return self.push_encoder(key, encoder)

    def write_date(
            self, key: str = None, tag: Hashable = None,
            value: Union[DateObject, datetime, date] = None, label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        value = DateObject.from_date_val(value)
        encoder = SimplePropertyEncoder.date(key, value)
        return self.push_encoder(key, encoder)

    def write_select(
            self, key: str = None, tag: Hashable = None, value: str = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = SimplePropertyEncoder.select(key, value)
        return self.push_encoder(key, encoder)

    def write_checkbox(
            self, key: str = None, tag: Hashable = None, value: bool = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = SimplePropertyEncoder.checkbox(key, value)
        return self.push_encoder(key, encoder)

    def write_number(
            self, key: str = None, tag: Hashable = None, value: Union[int, float] = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = SimplePropertyEncoder.number(key, value)
        return self.push_encoder(key, encoder)

    def write_phone_number(
            self, key: str = None, tag: Hashable = None, value: str = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = SimplePropertyEncoder.phone_number(key, value)
        return self.push_encoder(key, encoder)

    def write_email(
            self, key: str = None, tag: Hashable = None, value: str = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = SimplePropertyEncoder.email(key, value)
        return self.push_encoder(key, encoder)

    def write_url(
            self, key: str = None, tag: Hashable = None, value: str = None,
            label: Hashable = None):
        key, value = self._cleaned_key_with_a_value(key, tag, value, label)
        encoder = SimplePropertyEncoder.url(key, value)
        return self.push_encoder(key, encoder)
