from abc import ABCMeta
from dataclasses import dataclass
from typing import Optional, Any

from notion_df.resource.core import Deserializable, set_master
from notion_df.resource.misc import UUID
from notion_df.util.misc import dict_filter_truthy


@set_master
@dataclass
class User(Deserializable, metaclass=ABCMeta):
    id: UUID
    name: Optional[str]
    avatar_url: Optional[str]

    def _plain_serialize(self) -> dict[str, Any]:
        return dict_filter_truthy({
            'object': 'user',
            'id': self.id,
            'name': self.name,
            'avatar_url': self.avatar_url,
        })


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
