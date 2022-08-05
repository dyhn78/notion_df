from __future__ import annotations

from abc import ABCMeta, abstractmethod

from notion_zap.cli.core.date_property_value import DatePropertyValue
from notion_zap.cli.core.mixins import ValueCarrier
from ..rich_text import RichTextObjectEncoder


class PropertyEncoder(ValueCarrier, metaclass=ABCMeta):
    def __init__(self, key, value_type):
        super().__init__()
        self.key = key
        self.value_type = value_type

    @property
    @abstractmethod
    def prop_value(self):
        pass

    @abstractmethod
    def plain_form(self) -> str:
        pass

    def __bool__(self):
        return bool(self.encode())

    def encode(self):
        props = {self.key: {self.value_type: self.prop_value,
                                  # 'type': self.value_type <- prior to 2021-08-16,
                                  }
                 }
        return props


class RichTextPropertyEncoder(PropertyEncoder, RichTextObjectEncoder):
    def __init__(self, key, data_type):
        PropertyEncoder.__init__(self, key, data_type)
        RichTextObjectEncoder.__init__(self)

    @property
    def prop_value(self):
        return RichTextObjectEncoder.encode(self)

    def plain_form(self):
        return RichTextObjectEncoder.plain_form(self)


class FilesPropertyEncoder(PropertyEncoder):
    def __init__(self, key):
        PropertyEncoder.__init__(self, key, 'files')
        self._prop_value = []
        self._plain_form = []

    def plain_form(self):
        return ''.join(self._plain_form)

    def add_file(self, file_name: str, file_url: str):
        new_value = {
            "type": "external",
            "name": file_name,
            "external": {'url': file_url}
        }
        self._prop_value.append(new_value)
        self._plain_form.append(file_name)

    @property
    def prop_value(self):
        return self._prop_value


class SimplePropertyEncoder(PropertyEncoder):
    def __init__(self, key, value, data_type):
        super().__init__(key=key, value_type=data_type)
        self._prop_value = value

    @property
    def prop_value(self):
        return self._prop_value

    def plain_form(self):
        return self._prop_value

    @classmethod
    def number(cls, key, value):
        return cls(key, value, 'number')

    @classmethod
    def checkbox(cls, key, value):
        return cls(key, value, 'checkbox')

    @classmethod
    def people(cls, key, value):
        return cls(key, value, 'people')

    @classmethod
    def url(cls, key, value):
        return cls(key, value, 'url')

    @classmethod
    def email(cls, key, value):
        return cls(key, value, 'email')

    @classmethod
    def phone_number(cls, key, value):
        return cls(key, value, 'phone_number')

    @classmethod
    def select(cls, key, value):
        wrapped_value = {'name': value} if value is not None else None
        return cls(key, wrapped_value, 'select')

    @classmethod
    def multi_select(cls, key, values: list[str]):
        wrapped_value = [{'name': option} for option in values]
        return cls(key, wrapped_value, 'multi_select')

    @classmethod
    def relation(cls, key, page_ids: list[str]):
        wrapped_value = [{'id': page_id} for page_id in page_ids]
        return cls(key, wrapped_value, 'relation')

    @classmethod
    def date(cls, key, value: DatePropertyValue):
        value = value.isoformat()
        return cls(key, value, 'date')
