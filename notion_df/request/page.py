from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from notion_df.resource.core import Deserializable
from notion_df.resource.file import ExternalFile
from notion_df.resource.misc import UUID, Icon
from notion_df.resource.parent import Parent
from notion_df.resource.property_value import PropertyValue
from notion_df.resource.rich_text import RichText
from notion_df.resource.user import PartialUser


@dataclass
class PageResponse(Deserializable):
    id: UUID
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    icon: Icon
    cover: ExternalFile
    url: str
    title: list[RichText]
    properties: dict[str, PropertyValue] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    parent: Parent
    archived: bool
    is_inline: bool

    def _plain_serialize(self) -> dict[str, Any]:
        return {
            "object": "page",
            "id": self.id,
            "created_time": self.created_by,
            "last_edited_time": self.last_edited_by,
            "created_by": self.created_by,
            "last_edited_by": self.last_edited_by,
            "cover": self.cover,
            "icon": self.icon,
            "parent": self.parent,
            "archived": False,
            "properties": self.properties,
            "url": self.url,
        }
