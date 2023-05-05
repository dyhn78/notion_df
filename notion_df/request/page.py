from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

from notion_df.core.request import SingleRequest, RequestSettings, Version, Method, MAX_PAGE_SIZE, \
    PaginatedRequest, BaseRequest
from notion_df.object.block import BlockType, serialize_partial_block_list
from notion_df.object.common import Icon, Properties
from notion_df.object.file import ExternalFile
from notion_df.object.page import PageProperty, page_property_registry, PageResponse, PageProperties
from notion_df.object.parent import ParentInfo
from notion_df.util.collection import DictFilter
from notion_df.util.misc import UUID


@dataclass
class RetrievePage(SingleRequest[PageResponse]):
    """https://developers.notion.com/reference/retrieve-a-page"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> None:
        return


@dataclass
class CreatePage(SingleRequest[PageResponse]):
    """https://developers.notion.com/reference/post-page"""
    parent: ParentInfo
    properties: PageProperties = field(default_factory=Properties)
    children: list[BlockType] = None
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
class RetrievePagePropertyItem(BaseRequest[PageProperty]):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    page_id: UUID
    property_id: UUID
    page_size: int = -1

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self) -> None:
        return

    request_once = PaginatedRequest.request_once

    def execute(self) -> PageProperty:
        # TODO: deduplicate with PaginatedRequest.execute() if possible.
        page_size_total = self.page_size
        if page_size_total == -1:
            page_size_total = float('inf')
        page_size = min(MAX_PAGE_SIZE, page_size_total)
        page_size_retrieved = page_size

        data = self.request_once(page_size, None)
        if data['object'] == 'property_item':
            return PageProperty.deserialize(data)

        data_list = []
        while page_size_retrieved < page_size_total and data['has_more']:
            start_cursor = data['next_cursor']
            page_size = min(MAX_PAGE_SIZE, page_size_total - page_size_retrieved)
            page_size_retrieved += page_size

            data = self.request_once(page_size, start_cursor)
            data_list.append(data)

        typename = data_list[0]['property_item']['type']
        subclass = page_property_registry[typename]
        value_list = [data['result'][typename] for data in data_list]
        merged_response = data_list[0]['result'] | {typename: value_list}
        return subclass.deserialize(merged_response)
