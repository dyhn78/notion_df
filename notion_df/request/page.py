from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Union

from typing_extensions import Self

from notion_df.object.block import BlockType
from notion_df.object.core import Deserializable
from notion_df.object.file import ExternalFile
from notion_df.object.misc import UUID, Icon
from notion_df.object.page import PageProperty, page_property_registry
from notion_df.object.parent import Parent
from notion_df.object.rich_text import RichText
from notion_df.object.user import User
from notion_df.request.core import Request, RequestSettings, Version, Method, MAX_PAGE_SIZE, \
    PaginatedRequest, BaseRequest


def deserialize_properties(response_data: dict[str, Union[Any, dict[str, Any]]]) -> dict[str, PageProperty]:
    properties = {}
    for prop_name, prop_serialized in response_data['properties'].items():
        prop = PageProperty.deserialize(prop_serialized)
        prop.name = prop_name
        properties[prop_name] = prop
    return properties


def serialize_partial_block_list(block_type_list: list[BlockType]) -> list[dict[str, Any]]:
    return [{
        "object": "block",
        "type": type_object,
        type_object.get_typename(): type_object,
    } for type_object in block_type_list]


@dataclass
class ResponsePage(Deserializable):
    id: UUID
    parent: Parent
    created_time: datetime
    last_edited_time: datetime
    created_by: User
    last_edited_by: User
    icon: Icon
    cover: ExternalFile
    url: str
    title: list[RichText]
    properties: dict[str, PageProperty] = field()
    archived: bool
    is_inline: bool

    @classmethod
    def _deserialize_this(cls, response_data: dict[str, Any]) -> Self:
        return cls._deserialize_asdict(response_data | {'properties': deserialize_properties(response_data)})


@dataclass
class RetrievePage(Request[ResponsePage]):
    """https://developers.notion.com/reference/retrieve-a-page"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class CreatePage(Request[ResponsePage]):
    """https://developers.notion.com/reference/post-page"""
    parent: Parent
    icon: Icon
    cover: ExternalFile
    properties: list[PageProperty] = field()
    children: list[BlockType] = field()

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/pages')

    def get_body(self) -> Any:
        return {
            "parent": self.parent,
            "icon": self.icon,
            "cover": self.cover,
            "properties": {prop.name: prop for prop in self.properties},
            "children": serialize_partial_block_list(self.children),
        }


@dataclass
class UpdatePage(Request[ResponsePage]):
    """https://developers.notion.com/reference/patch-page"""
    id: UUID
    icon: Icon
    cover: ExternalFile
    properties: list[PageProperty] = field()
    archived: bool

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> Any:
        return {
            "icon": self.icon,
            "cover": self.cover,
            "properties": {prop.name: prop for prop in self.properties},
            "archived": self.archived,
        }


@dataclass
class RetrievePagePropertyItem(BaseRequest[PageProperty]):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    page_id: UUID
    property_id: UUID
    page_size: int = -1

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self):
        pass

    request_once = PaginatedRequest.request_once

    def request(self):
        # TODO: deduplicate with PaginatedRequest.request() if possible.
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
