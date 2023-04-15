from dataclasses import dataclass, field
from typing import Any

from notion_df.request.core import Request, RequestSettings, Version, Method, MAX_PAGE_SIZE, \
    PaginatedRequest, BaseRequest
from notion_df.response.block import BlockType
from notion_df.response.file import ExternalFile
from notion_df.response.misc import UUID, Icon
from notion_df.response.page import ResponsePage, PageProperty
from notion_df.response.parent import Parent


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
            "children": [{
                "object": "block",
                "type": type_object,
                type_object.get_type(): type_object,
            } for type_object in self.children],
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

        return PageProperty.deserialize_property_item_list(data_list)
