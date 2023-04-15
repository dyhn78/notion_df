from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Any

from typing_extensions import Self

from notion_df.response.core import Deserializable
from notion_df.response.misc import UUID


@dataclass
class User(Deserializable, metaclass=ABCMeta):
    """field with `init=False` are those not required from user-side but provided from server-side."""
    id: UUID
    name: str = field(init=False)
    avatar_url: str = field(init=False)

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            'object': 'user',
            'id': self.id,
        }

    @classmethod
    def _plain_deserialize(cls, serialized: dict[str, Any], **field_value_presets: Any) -> Self:
        plain_self = cls._plain_deserialize(serialized)
        plain_self.name = serialized['name']
        plain_self.avatar_url = serialized['avatar_url']
        return plain_self

    @classmethod
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        typename = serialized['type']
        if typename == 'person':
            subclass = Person
        else:
            bot_owner_typename = serialized['bot']['owner']['type']
            if bot_owner_typename == 'workspace':
                subclass = WorkspaceBot
            else:
                subclass = UserBot
        return subclass.deserialize(serialized)


@dataclass
class Person(User):
    email: str

    def _plain_serialize(self) -> dict[str, Any]:
        return super()._plain_serialize() | {
            'type': 'person',
            'person': {
                'email': self.email
            }
        }


@dataclass
class WorkspaceBot(User):
    def _plain_serialize(self) -> dict[str, Any]:
        return super()._plain_serialize() | {
            "type": "bot",
            "bot": {
                "owner": {"type": "workspace"},
                "workspace_name": "Ada Lovelace’s Notion"
            }
        }


@dataclass
class UserBot(User):
    def _plain_serialize(self) -> dict[str, Any]:
        return super()._plain_serialize() | {
            "type": "bot",
            "bot": {
                "owner": {"type": "user"},
                "workspace_name": None
            }
        }
