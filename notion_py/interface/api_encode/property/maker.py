from __future__ import annotations
from abc import ABCMeta, abstractmethod

from notion_py.interface.api_encode.rich_text import RichTextObjectEncoder
from notion_py.interface.struct import ValueCarrier, DateFormat


class PropertyEncoder(ValueCarrier, metaclass=ABCMeta):
    def __init__(self, value_type, prop_name):
        super().__init__()
        self.prop_name = prop_name
        self.value_type = value_type

    @property
    @abstractmethod
    def _prop_value(self):
        pass

    def __bool__(self):
        return bool(self.unpack())

    def unpack(self):
        props = {self.prop_name: {self.value_type: self._prop_value,
                                  # 'type': self.value_type,
                                  }
                 }
        return props


class RichTextPropertyEncoder(PropertyEncoder, RichTextObjectEncoder):
    def __init__(self, prop_type, prop_name):
        PropertyEncoder.__init__(self, prop_type, prop_name)
        RichTextObjectEncoder.__init__(self)

    @property
    def _prop_value(self):
        return RichTextObjectEncoder.unpack(self)


class SimplePropertyEncoder(PropertyEncoder):
    def __init__(self, prop_type, prop_name, value):
        super().__init__(prop_type, prop_name)
        self._value = value

    @property
    def _prop_value(self):
        return self._value

    @classmethod
    def number(cls, prop_name, value):
        return cls('number', prop_name, value)

    @classmethod
    def checkbox(cls, prop_name, value):
        return cls('checkbox', prop_name, value)

    @classmethod
    def files(cls, prop_name, value):
        # TODO : 새 API 활용
        return cls('files', prop_name, value)

    @classmethod
    def people(cls, prop_name, value):
        return cls('people', prop_name, value)

    @classmethod
    def url(cls, prop_name, value):
        return cls('url', prop_name, value)

    @classmethod
    def email(cls, prop_name, value):
        return cls('email', prop_name, value)

    @classmethod
    def phone_number(cls, prop_name, value):
        return cls('phone_number', prop_name, value)

    @classmethod
    def select(cls, prop_name, value):
        return cls('select', prop_name, {'name': value})

    @classmethod
    def multi_select(cls, prop_name, values: list[str]):
        prop_value = [{'name': value} for value in values]
        return cls('multi_select', prop_name, prop_value)

    @classmethod
    def relation(cls, prop_name, page_ids: list[str]):
        prop_value = [{'id': page_id} for page_id in page_ids]
        return cls('relation', prop_name, prop_value)

    @classmethod
    def date(cls, prop_name, value: DateFormat):
        prop_value = value.make_isoformat()
        return cls('date', prop_name, prop_value)
