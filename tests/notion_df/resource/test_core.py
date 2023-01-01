from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime

import pytest
import pytz

from notion_df.resource.core import Deserializable, deserialize_any, master, deserializable_registry
from notion_df.util.collection import StrEnum, KeyChain
from notion_df.variables import Variables


def test__find_type_keychain():
    assert deserializable_registry.get_type_keychain({'type': 'checkbox', 'checkbox': True}) == KeyChain(('checkbox',))
    assert deserializable_registry.get_type_keychain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == KeyChain(('mention', 'user'))


def test__typed_resource__simple():
    @dataclass
    @master
    class TypedResource(Deserializable, metaclass=ABCMeta):
        pass

    @dataclass
    class __TestResource(TypedResource):
        content: str
        link: str

        def plain_serialize(self):
            return {
                'type': 'text',
                'text': {
                    'content': self.content,
                    'link': {
                        'type': 'url',
                        'url': self.link
                    } if self.link else None
                }
            }

    assert deserializable_registry._data[TypedResource][KeyChain(('text',))] == __TestResource
    assert __TestResource._field_keychain_dict == {
        ('text', 'content'): 'content',
        ('text', 'link', 'url'): 'link',
    }
    assert TypedResource.deserialize({
        'type': 'text',
        'text': {
            'content': 'self.content',
            'link': {
                'type': 'url',
                'url': 'self.link'
            }
        }
    }) == __TestResource('self.content', 'self.link')


def test_resource__call_its_method():
    @dataclass
    @master
    class TypedResource(Deserializable, metaclass=ABCMeta):
        pass

    @dataclass
    class __TestResource(TypedResource):
        user_id: str

        def plain_serialize(self):
            return {
                'type': 'mention',
                'mention': self._serialize_inner_value()
            }

        def _serialize_inner_value(self):
            return {
                'type': 'user',
                'user': {
                    'object': 'user',
                    'id': self.user_id
                }
            }

    assert deserializable_registry._data[TypedResource][KeyChain(('mention', 'user'))] == __TestResource
    assert __TestResource._field_keychain_dict == {
        ('mention', 'user', 'id'): 'user_id'
    }
    with pytest.raises(KeyError):
        TypedResource.deserialize({
            'type': 'text',
            'text': {
                'content': 'self.content',
                'link': {
                    'type': 'url',
                    'url': 'self.link'
                }
            }
        })


def test_resource__external():
    @dataclass
    class __TestDeserializable(Deserializable):
        start: datetime
        end: datetime

        def plain_serialize(self):
            return {
                'start': self.start,
                'end': self.end,
            }

    Variables.timezone = pytz.utc
    resource = __TestDeserializable(datetime(2022, 1, 1), datetime(2023, 1, 1))
    serialized = {'start': '2022-01-01T00:00:00', 'end': '2023-01-01T00:00:00'}
    assert resource.serialize() == serialized
    assert deserialize_any(serialized, __TestDeserializable) == resource


def test_resource__external_2():
    class _Color(StrEnum):
        default = 'default'
        gray = 'gray'

    @dataclass
    class _Link(Deserializable):
        value: str

        def plain_serialize(self):
            return {'value': self.value}

    @dataclass
    class __TestDeserializable(Deserializable):
        url: str
        hrefs: dict[str, _Link] = field(default_factory=dict)
        bold: bool = False
        color: _Color = _Color.default
        link: _Link = None

        def plain_serialize(self):
            return {
                'url1': self.url,
                'bold1': self.bold,
                'color1': self.color,
                'link': self.link,
                'hrefs': self.hrefs
            }

    resource = __TestDeserializable(url='url', bold=True, link=_Link('link'), color=_Color.gray,
                                    hrefs={'a': _Link('a'), 'b': _Link('b')})
    serialized = {'url1': 'url', 'bold1': True, 'link': {'value': 'link'}, 'color1': 'gray',
                  'hrefs': {'a': {'value': 'a'}, 'b': {'value': 'b'}}}
    assert resource.serialize() == serialized
    assert deserialize_any(serialized, __TestDeserializable) == resource
