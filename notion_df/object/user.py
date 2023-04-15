from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, final

from typing_extensions import Self

from notion_df.object.core import DualSerializable
from notion_df.object.misc import UUID


@dataclass
class User(DualSerializable, metaclass=ABCMeta):
    """field with `init=False` are those not required from user-side but provided from server-side."""
    id: UUID
    name: str = field(init=False)
    avatar_url: str = field(init=False)

    @classmethod
    @abstractmethod
    def _deserialize_main(cls, serialized: dict[str, Any]) -> Self:
        pass

    @classmethod
    @final
    def deserialize(cls, serialized: dict[str, Any]) -> Self:
        def get_subclass() -> type[User]:
            typename = serialized['type']
            if typename == 'person':
                return Person
            else:
                bot_owner_typename = serialized['bot']['owner']['type']
                if bot_owner_typename == 'workspace':
                    return WorkspaceBot
                else:
                    return UserBot

        self = get_subclass()._deserialize_main(serialized)
        self.name = serialized['name']
        self.avatar_url = serialized['avatar_url']
        return self


@dataclass
class Person(User):
    email: str

    def serialize(self) -> dict[str, Any]:
        return {
            'object': 'user',
            'id': self.id,
            'type': 'person',
            'person': {
                'email': self.email
            }
        }

    @classmethod
    def _deserialize_main(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['id'], serialized['person']['email'])


@dataclass
class WorkspaceBot(User):
    workspace_name: str

    def serialize(self) -> dict[str, Any]:
        return {
            'object': 'user',
            'id': self.id,
            "type": "bot",
            "bot": {
                "owner": {"type": "workspace"},
                "workspace_name": self.workspace_name,
            }
        }

    @classmethod
    def _deserialize_main(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['id'], serialized['bot']['workspace_name'])


@dataclass
class UserBot(User):
    def serialize(self) -> dict[str, Any]:
        return {
            'object': 'user',
            'id': self.id,
            "type": "bot",
            "bot": {
                "owner": {"type": "user"},
                "workspace_name": None
            }
        }

    @classmethod
    def _deserialize_main(cls, serialized: dict[str, Any]) -> Self:
        return cls(serialized['id'])
