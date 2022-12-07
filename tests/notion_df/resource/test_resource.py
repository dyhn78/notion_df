from dataclasses import dataclass

import pytest

from notion_df.resource.core import Resource


def test_resource__find_type_key_chain():
    assert Resource._get_type_key_chain({'type': 'checkbox', 'checkbox': True}) == ('checkbox',)
    assert Resource._get_type_key_chain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == ('mention', 'user')


def test_resource__init_subclass__simple():
    @dataclass
    class __TestResource(Resource):
        content: str
        link: str

        def to_dict(self):
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

    assert Resource._registry[('text',)] == __TestResource
    assert __TestResource._attr_name_dict == {
        ('text', 'content'): 'content',
        ('text', 'link', 'url'): 'link',
    }
    assert Resource.from_dict({
        'type': 'text',
        'text': {
            'content': 'self.content',
            'link': {
                'type': 'url',
                'url': 'self.link'
            }
        }
    }) == __TestResource('self.content', 'self.link')


def test_resource__init_subclass__complex():
    @dataclass
    class __TestResource(Resource):
        user_id: str

        def to_dict(self):
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
        Resource.from_dict({
            'type': 'text',
            'text': {
                'content': 'self.content',
                'link': {
                    'type': 'url',
                    'url': 'self.link'
                }
            }
        })
