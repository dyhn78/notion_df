from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Optional
from uuid import UUID

from typing_extensions import Self

from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile
from notion_df.object.parent import ParentInfo
from notion_df.object.property_depr import PageProperties
from notion_df.object.user import PartialUser
from notion_df.request.core import Response


@dataclass
class PageResponse(Response):
    id: UUID
    parent: ParentInfo
    created_time: datetime
    last_edited_time: datetime
    created_by: PartialUser
    last_edited_by: PartialUser
    archived: bool
    icon: Optional[Icon]
    cover: Optional[ExternalFile]
    url: str
    properties: PageProperties

    @classmethod
    def _deserialize_this(cls, response_data: dict[str, Any]) -> Self:
        return cls._deserialize_from_dict(response_data)
