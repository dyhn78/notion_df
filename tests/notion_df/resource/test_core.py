from dataclasses import dataclass
from datetime import datetime

import pytest

from notion_df.resource.core import Resource, serialize


def test_resource__find_type_key_chain():
    assert Resource._get_type_key_chain({'type': 'checkbox', 'checkbox': True}) == ('checkbox',)
    assert Resource._get_type_key_chain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == ('mention', 'user')


def test_resource__simple():
    @dataclass
    class __TestResource(Resource):
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

    print(Resource._registry)

    assert Resource._registry[('text',)] == __TestResource
    assert __TestResource._attr_name_dict == {
        ('text', 'content'): 'content',
        ('text', 'link', 'url'): 'link',
    }
    assert Resource.deserialize({
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
    Resource._registry.clear()

    @dataclass
    class __TestResource(Resource):
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

    assert Resource._registry[('mention', 'user')] == __TestResource
    assert __TestResource._attr_name_dict == {
        ('mention', 'user', 'id'): 'user_id'
    }
    with pytest.raises(KeyError):
        Resource.deserialize({
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
    class DatePropertyValue(Resource):
        # timezone option is disabled. you should handle timezone inside 'start' and 'end'.
        start: datetime
        end: datetime

        def serialize(self):
            return {
                'start': serialize(self.start),
                'end': serialize(self.end),
            }
