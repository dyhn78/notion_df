from abc import ABCMeta
from dataclasses import dataclass, field
from datetime import datetime

import pytest
import pytz

from notion_df.resource.core import Deserializable, deserialize, resolve_by_keychain, DeserializableResolverByKeyChain
from notion_df.util.collection import StrEnum, KeyChain
from notion_df.util.misc import NotionDfValueError
from notion_df.variables import Variables


@pytest.fixture
def master_deserializable() -> type[Deserializable]:
    @dataclass
    @resolve_by_keychain('type')
    class MasterDeserializable(Deserializable, metaclass=ABCMeta):
        pass

    return MasterDeserializable


def test__find_type_keychain():
    assert DeserializableResolverByKeyChain.resolve_keychain({'type': 'checkbox', 'checkbox': True}, 'type') == KeyChain(
        ('checkbox',))
    assert DeserializableResolverByKeyChain.resolve_keychain({'type': 'mention', 'mention': {
        'type': 'user',
        'user': {
            'object': 'user',
            'id': 'some_user_id'
        }
    }}, 'type') == KeyChain(('mention', 'user'))


def test__deserializer__simple(master_deserializable):
    @dataclass
    class TestDeserializable(master_deserializable):
        content: str
        link: str

        def _plain_serialize(self):
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

    assert master_deserializable.resolver.subclass_dict[KeyChain(('text',))] == TestDeserializable
    assert TestDeserializable._field_keychain_dict == {
        ('text', 'content'): 'content',
        ('text', 'link', 'url'): 'link',
    }
    assert master_deserializable.deserialize({
        'type': 'text',
        'text': {
            'content': 'self.content',
            'link': {
                'type': 'url',
                'url': 'self.link'
            }
        }
    }) == TestDeserializable('self.content', 'self.link')


def test_deserializable__call_method(master_deserializable):
    @dataclass
    class TestDeserializable(master_deserializable):
        user_id: str

        def _plain_serialize(self):
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

    assert master_deserializable.resolver.subclass_dict[KeyChain(('mention', 'user'))] \
           == TestDeserializable
    assert TestDeserializable._field_keychain_dict == {
        ('mention', 'user', 'id'): 'user_id'
    }
    with pytest.raises(NotionDfValueError):
        master_deserializable.deserialize({
            'type': 'text',
            'text': {
                'content': 'self.content',
                'link': {
                    'type': 'url',
                    'url': 'self.link'
                }
            }
        })


def test_deserializable__datetime():
    @dataclass
    class TestDeserializable(Deserializable):
        start: datetime
        end: datetime

        def _plain_serialize(self):
            return {
                'start': self.start,
                'end': self.end,
            }

    Variables.timezone = pytz.utc
    deserializable = TestDeserializable(datetime(2022, 1, 1), datetime(2023, 1, 1))
    serialized = {'start': '2022-01-01T00:00:00', 'end': '2023-01-01T00:00:00'}
    # TODO
    # assert deserializable.serialize() == serialized
    # assert deserialize(serialized, TestDeserializable) == deserializable


def test_deserializable__collections():
    class TestColor(StrEnum):
        default = 'default'
        gray = 'gray'

    @dataclass
    class TestLink(Deserializable):
        value: str

        def _plain_serialize(self):
            return {'value': self.value}

    @dataclass
    class TestDeserializable(Deserializable):
        url: str
        hrefs: dict[str, TestLink] = field(default_factory=dict)
        bold: bool = False
        color: TestColor = TestColor.default
        link: TestLink = None

        def _plain_serialize(self):
            return {
                'url1': self.url,
                'bold1': self.bold,
                'color1': self.color,
                'link': self.link,
                'hrefs': self.hrefs
            }

    deserializable = TestDeserializable(url='url', bold=True, link=TestLink('link'), color=TestColor.gray,
                                        hrefs={'a': TestLink('a'), 'b': TestLink('b')})
    serialized = {'url1': 'url', 'bold1': True, 'link': {'value': 'link'}, 'color1': 'gray',
                  'hrefs': {'a': {'value': 'a'}, 'b': {'value': 'b'}}}
    assert deserializable.serialize() == serialized
    assert deserialize(serialized, TestDeserializable) == deserializable
