import functools
from abc import ABCMeta
from dataclasses import dataclass, field
from typing import Any, final
from uuid import UUID

from typing_extensions import Self

from notion_df.core.serialization import DualSerializable


@dataclass
class PartialUser(DualSerializable):  # TODO: User
    id: UUID

    def serialize(self) -> dict[str, Any]:
        return {"object": "user", "id": str(self.id)}

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(UUID(raw["id"]))


@dataclass
class User(DualSerializable, metaclass=ABCMeta):  # TODO: UserData
    id: UUID
    name: str = field(init=False, default=None)
    avatar_url: str = field(init=False, default=None)

    def __init_subclass__(cls, **kwargs) -> None:
        super().__init_subclass__(**kwargs)
        _deserialize_this = cls._deserialize_this

        @functools.wraps(_deserialize_this)
        def _deserialize_this_wrapped(raw: dict[str, Any]):
            self = _deserialize_this(raw)
            self.name = raw["name"]
            self.avatar_url = raw["avatar_url"]
            return self

        setattr(cls, "_deserialize_this", _deserialize_this_wrapped)

    @classmethod
    @final
    def _deserialize_subclass(cls, raw: dict[str, Any]) -> Self:
        def get_subclass() -> type[User]:
            typename = raw["type"]
            if typename == "person":
                return Person
            else:
                bot_owner_typename = raw["bot"]["owner"]["type"]
                if bot_owner_typename == "workspace":
                    return WorkspaceBot
                else:
                    return UserBot

        return get_subclass()._deserialize_this(raw)


@dataclass
class Person(User):
    email: str

    def serialize(self) -> dict[str, Any]:
        return {
            "object": "user",
            "id": self.id,
            "type": "person",
            "person": {"email": self.email},
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["id"], raw["person"]["email"])


@dataclass
class WorkspaceBot(User):
    workspace_name: str

    def serialize(self) -> dict[str, Any]:
        return {
            "object": "user",
            "id": self.id,
            "type": "bot",
            "bot": {
                "owner": {"type": "workspace"},
                "workspace_name": self.workspace_name,
            },
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["id"], raw["bot"]["workspace_name"])


@dataclass
class UserBot(User):
    def serialize(self) -> dict[str, Any]:
        return {
            "object": "user",
            "id": self.id,
            "type": "bot",
            "bot": {"owner": {"type": "user"}, "workspace_name": None},
        }

    @classmethod
    def _deserialize_this(cls, raw: dict[str, Any]) -> Self:
        return cls(raw["id"])
