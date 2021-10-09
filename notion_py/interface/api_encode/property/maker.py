from __future__ import annotations
from abc import ABCMeta, abstractmethod

from notion_py.interface.api_encode.rich_text import RichTextObjectEncoder
from notion_py.interface.struct import ValueCarrier, DateFormat


class PropertyEncoder(ValueCarrier, metaclass=ABCMeta):
    def __init__(self, prop_name, value_type):
        super().__init__()
        self.prop_name = prop_name
        self.value_type = value_type

    @property
    @abstractmethod
    def prop_value(self):
        pass

    def __bool__(self):
        return bool(self.unpack())

    def unpack(self):
        props = {self.prop_name: {self.value_type: self.prop_value,
                                  # 'type': self.value_type <- prior to 2021-08-16,
                                  }
                 }
        return props


class RichTextPropertyEncoder(PropertyEncoder, RichTextObjectEncoder):
    def __init__(self, prop_name, prop_type):
        PropertyEncoder.__init__(self, prop_name, prop_type)
        RichTextObjectEncoder.__init__(self)

    @property
    def prop_value(self):
        return RichTextObjectEncoder.unpack(self)


class FilesPropertyEncoder(PropertyEncoder):
    def __init__(self, prop_name):
        PropertyEncoder.__init__(self, prop_name=prop_name, value_type='files')
        self._prop_value = []

    def add_file(self, file_name: str, file_url: str):
        new_value = {
            "type": "external",
            "name": file_name,
            "external": {'url': file_url}
        }
        self._prop_value.append(new_value)

    @property
    def prop_value(self):
        return self._prop_value


class SimplePropertyEncoder(PropertyEncoder):
    def __init__(self, prop_name, prop_type, value):
        super().__init__(prop_name=prop_name, value_type=prop_type)
        self._prop_value = value

    @property
    def prop_value(self):
        return self._prop_value

    @classmethod
    def number(cls, prop_name, value):
        return cls(prop_name, 'number', value)

    @classmethod
    def checkbox(cls, prop_name, value):
        return cls(prop_name, 'checkbox', value)

    @classmethod
    def files(cls, prop_name, value):
        # TODO : 새 API 활용
        return cls(prop_name, 'files', value)

    @classmethod
    def people(cls, prop_name, value):
        return cls(prop_name, 'people', value)

    @classmethod
    def url(cls, prop_name, value):
        return cls(prop_name, 'url', value)

    @classmethod
    def email(cls, prop_name, value):
        return cls(prop_name, 'email', value)

    @classmethod
    def phone_number(cls, prop_name, value):
        return cls(prop_name, 'phone_number', value)

    @classmethod
    def select(cls, prop_name, value):
        return cls(prop_name, 'select', {'name': value})

    @classmethod
    def multi_select(cls, prop_name, values: list[str]):
        prop_value = [{'name': value} for value in values]
        return cls(prop_name, 'multi_select', prop_value)

    @classmethod
    def relation(cls, prop_name, page_ids: list[str]):
        prop_value = [{'id': page_id} for page_id in page_ids]
        return cls(prop_name, 'relation', prop_value)

    @classmethod
    def date(cls, prop_name, value: DateFormat):
        prop_value = value.make_isoformat()
        return cls('date', prop_name, prop_value)
