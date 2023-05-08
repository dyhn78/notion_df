from abc import ABCMeta, abstractmethod
from dataclasses import dataclass, field
from typing import Any, final
from uuid import UUID

from typing_extensions import Self

from notion_df.util.serialization import DualSerializable


@dataclass
class PartialUser(DualSerializable):
    id: UUID

    def serialize(self) -> dict[str, Any]:
        return {
            'object': 'user',
            'id': self.id
        }

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        return cls(UUID(serialized['id']))


@dataclass
class User(DualSerializable, metaclass=ABCMeta):
    id: UUID
    name: str = field(init=False, default=None)
    avatar_url: str = field(init=False, default=None)

    @classmethod
    def _deserialize_this(cls, serialized: dict[str, Any]) -> Self:
        self = cls._deserialize_main(serialized)
        self.name = serialized['name']
        self.avatar_url = serialized['avatar_url']
        return self

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

        return get_subclass()._deserialize_this(serialized)


class Users(list[User]):
    def __init__(self, users: list[User]):
        super().__init__(users)


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
