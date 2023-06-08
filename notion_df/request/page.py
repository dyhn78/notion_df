from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from notion_df.object.block import BlockValue, serialize_partial_block_list, PageResponse
from notion_df.object.common import Icon
from notion_df.object.file import ExternalFile
from notion_df.object.partial_parent import PartialParent
from notion_df.object.property import PageProperties, Property, PropertyValue_T
from notion_df.core.request import SingleRequest, RequestSettings, Version, Method, PaginatedRequest, \
    BaseRequest
from notion_df.util.collection import DictFilter


@dataclass
class RetrievePage(SingleRequest[PageResponse]):
    """https://developers.notion.com/reference/retrieve-a-page"""
    id: UUID
    response_type = PageResponse

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> None:
        return


@dataclass
class CreatePage(SingleRequest[PageResponse]):
    """https://developers.notion.com/reference/post-page"""
    response_type = PageResponse
    parent: PartialParent
    properties: PageProperties = field(default_factory=PageProperties)
    children: list[BlockValue] = None
    icon: Optional[Icon] = field(default=None)
    cover: Optional[ExternalFile] = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/pages')

    def get_body(self) -> dict[str, Any]:
        return DictFilter.not_none({
            "parent": self.parent,
            "icon": self.icon,
            "cover": self.cover,
            "properties": self.properties,
            "children": serialize_partial_block_list(self.children),
        })


@dataclass
class UpdatePage(SingleRequest[PageResponse]):
    """https://developers.notion.com/reference/patch-page"""
    response_type = PageResponse
    id: UUID
    properties: Optional[PageProperties] = None
    """send empty PageProperty to delete all properties."""
    icon: Optional[Icon] = field(default=None)
    cover: Optional[ExternalFile] = field(default=None)
    archived: Optional[bool] = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> dict[str, Any]:
        return DictFilter.not_none({
            "icon": self.icon,
            "cover": self.cover,
            "properties": self.properties,
            "archived": self.archived,
        })


@dataclass
class RetrievePagePropertyItem(BaseRequest):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    # for simplicity reasons, pagination is not supported.
    page_id: UUID
    property_id: str

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self) -> None:
        return

    execute_once = PaginatedRequest.execute_once

    def execute(self) -> PropertyValue_T:
        data = self.execute_once()
        if (prop_serialized := data)['object'] == 'property_item':
            # noinspection PyProtectedMember
            return Property._deserialize_page(prop_serialized)

        data_list = []
        while data['has_more']:
            start_cursor = data['next_cursor']
            data = self.execute_once(start_cursor=start_cursor)
            data_list.append(data)

        typename = data_list[0]['property_item']['type']
        value_list = [data['result'][typename] for data in data_list]
        merged_prop_serialized = {**data_list[0]['result'], 'type': typename, typename: value_list}
        # noinspection PyProtectedMember
        return Property._deserialize_page(merged_prop_serialized)
