from dataclasses import dataclass

from notion_df.resource.resource import Resource, ResourceParser, get_type_key_chain


def test_resource_find_type_key_chain():
    assert get_type_key_chain({'type': 'checkbox', 'checkbox': True}) == ('checkbox',)
    assert get_type_key_chain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}) == ('mention', 'user')


def test_resource_mock__simple():
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

    assert ResourceParser(__TestResource).to_dict == {
        'type': 'text',
        'text': {
            'content': 'self.content',
            'link': {
                'type': 'url',
                'url': 'self.link'
            } if 'self.link' else None
        }
    }


def test_resource_mock__complex():
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

    assert ResourceParser(__TestResource).to_dict == {
        'type': 'mention',
        'mention': {
            'type': 'user',
            'user': {
                'object': 'user',
                'id': 'self.user_id'
            }
        }
    }
