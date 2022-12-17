from dataclasses import dataclass, field
from datetime import datetime

import pytest

from notion_df.resource.core import TypedResource, Resource, deserialize
from notion_df.util.collection import StrEnum


def test_resource__find_type_keychain():
    assert TypedResource._get_type_keychain({'type': 'checkbox', 'checkbox': True}) == ('checkbox',)
    assert TypedResource._get_type_keychain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == ('mention', 'user')


def test_resource__simple():
    @dataclass
    class __TestResource(TypedResource):
        content: str
        link: str

        def serialize(self):
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
    assert TypedResource._registry[('text',)] == __TestResource
    assert __TestResource._attr_location_dict == {
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

        def serialize(self):
            return {
                'type': 'mention',
                'mention': self._mention_to_dict()
            }

        def _mention_to_dict(self):
            return {
                'type': 'user',
                'user': {
                    'object': 'user',
                    'id': self.user_id
                }
            }

    assert TypedResource._registry[('mention', 'user')] == __TestResource
    assert __TestResource._attr_location_dict == {
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
    class __TestResource(Resource):
        start: datetime
        end: datetime

        def serialize(self):
            return {
                'start': self.start,
                'end': self.end,
            }

    resource = __TestResource(datetime(2022, 1, 1), datetime(2023, 1, 1))
    serialized = {'start': '2022-01-01T00:00:00', 'end': '2023-01-01T00:00:00'}
    assert resource.serialize() == serialized
    assert deserialize(serialized, __TestResource) == resource


def test_resource__external_2():
    class _Color(StrEnum):
        default = 'default'
        gray = 'gray'

    @dataclass
    class _Link(Resource):
        value: str

        def serialize(self):
            return {'value': self.value}

    @dataclass
    class __TestResource(Resource):
        url: str
        hrefs: dict[str, _Link] = field(default_factory=dict)
        bold: bool = False
        color: _Color = _Color.default
        link: _Link = None

        def serialize(self):
            return {
                'url1': self.url,
                'bold1': self.bold,
                'color1': self.color,
                'link': self.link,
                'hrefs': self.hrefs
            }

    resource = __TestResource(url='url', bold=True, link=_Link('link'), color=_Color.gray,
                              hrefs={'a': _Link('a'), 'b': _Link('b')})
    serialized = {'url1': 'url', 'bold1': True, 'link': {'value': 'link'}, 'color1': 'gray',
                  'hrefs': {'a': {'value': 'a'}, 'b': {'value': 'b'}}}
    assert resource.serialize() == serialized
    assert deserialize(serialized, __TestResource) == resource
