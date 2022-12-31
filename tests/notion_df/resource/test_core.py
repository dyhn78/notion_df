from dataclasses import dataclass, field
from datetime import datetime

import pytest
import pytz

from notion_df.resource.core import TypedResource, DualResource, deserialize_any
from notion_df.util.collection import StrEnum, KeyChain
from notion_df.variables import Variables


def test_resource__find_type_keychain():
    assert TypedResource._get_type_keychain({'type': 'checkbox', 'checkbox': True}) == KeyChain(('checkbox',))
    assert TypedResource._get_type_keychain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == KeyChain(('mention', 'user'))


def test_resource__simple():
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
    print(TypedResource._registry)
    assert TypedResource._registry[KeyChain(('text',))] == __TestResource
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
    TypedResource._registry.clear()

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

    assert TypedResource._registry[KeyChain(('mention', 'user'))] == __TestResource
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
    class __TestDualResource(DualResource):
        start: datetime
        end: datetime

        def plain_serialize(self):
            return {
                'start': self.start,
                'end': self.end,
            }

    Variables.timezone = pytz.utc
    resource = __TestDualResource(datetime(2022, 1, 1), datetime(2023, 1, 1))
    serialized = {'start': '2022-01-01T00:00:00', 'end': '2023-01-01T00:00:00'}
    assert resource.serialize() == serialized
    assert deserialize_any(serialized, __TestDualResource) == resource


def test_resource__external_2():
    class _Color(StrEnum):
        default = 'default'
        gray = 'gray'

    @dataclass
    class _Link(DualResource):
        value: str

        def plain_serialize(self):
            return {'value': self.value}

    @dataclass
    class __TestDualResource(DualResource):
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

    resource = __TestDualResource(url='url', bold=True, link=_Link('link'), color=_Color.gray,
                                  hrefs={'a': _Link('a'), 'b': _Link('b')})
    serialized = {'url1': 'url', 'bold1': True, 'link': {'value': 'link'}, 'color1': 'gray',
                  'hrefs': {'a': {'value': 'a'}, 'b': {'value': 'b'}}}
    assert resource.serialize() == serialized
    assert deserialize_any(serialized, __TestDualResource) == resource
