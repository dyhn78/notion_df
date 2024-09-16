from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional
from uuid import UUID

from notion_df.contents import BlockContents, serialize_block_contents_list
from notion_df.core.collection import DictFilter
from notion_df.core.request import SingleRequestBuilder, RequestSettings, Version, \
    Method, RequestBuilder, request_page
from notion_df.data import PageData
from notion_df.file import ExternalFile
from notion_df.misc import Icon, PartialParent
from notion_df.property import PageProperties, Property, property_registry, PVT


@dataclass
class RetrievePage(SingleRequestBuilder[PageData]):
    """https://developers.notion.com/reference/retrieve-a-page"""
    id: UUID
    data_type = PageData

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'pages/{self.id}')

    def get_body(self) -> None:
        return


@dataclass
class CreatePage(SingleRequestBuilder[PageData]):
    """https://developers.notion.com/reference/post-page"""
    data_type = PageData
    parent: PartialParent
    properties: PageProperties = field(default_factory=PageProperties)
    children: list[BlockContents] = None
    icon: Optional[Icon] = field(default=None)
    cover: Optional[ExternalFile] = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'pages')

    def get_body(self) -> dict[str, Any]:
        return DictFilter.not_none({
            "parent": self.parent.serialize(),
            "icon": self.icon.serialize() if self.icon else None,
            "cover": self.cover.serialize() if self.cover else None,
            "properties": self.properties.serialize() if self.properties else None,
            "children": serialize_block_contents_list(self.children),
        })


@dataclass
class UpdatePage(SingleRequestBuilder[PageData]):
    """https://developers.notion.com/reference/patch-page"""
    # TODO: inspect that UpdatePage.response immediately update the page.data status ? (b031c3a)
    data_type = PageData
    id: UUID
    properties: Optional[PageProperties] = None
    """send empty PageProperty to delete all properties."""
    icon: Optional[Icon] = field(default=None)
    cover: Optional[ExternalFile] = field(default=None)
    archived: Optional[bool] = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'pages/{self.id}')

    def get_body(self) -> dict[str, Any]:
        return DictFilter.not_none({
            "icon": self.icon.serialize() if self.icon else None,
            "cover": self.cover.serialize() if self.cover else None,
            "properties": self.properties.serialize() if self.properties else None,
            "archived": self.archived,
        })


@dataclass
class RetrievePagePropertyItem(RequestBuilder):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    # for simplicity reasons, pagination is not supported.
    page_id: UUID
    property_id: str

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self) -> None:
        return

    def execute(self) -> tuple[Property[Any, PVT, Any], PVT, dict[str, Any]]:
        data = request_page(self)
        if (prop_serialized := data)['object'] == 'property_item':
            # noinspection PyProtectedMember
            return Property._deserialize_page_value(prop_serialized)

        data_list = [data]
        while data['has_more']:
            start_cursor = data['next_cursor']
            data = request_page(self, start_cursor=start_cursor)
            data_list.append(data)

        typename = data_list[0]['property_item']['type']
        raw_value_list = []
        for data in data_list:
            for result in data['results']:
                raw_value_list.append(result[typename])
        prop_serialized = {'type': typename, typename: raw_value_list, 'has_more': False}

        # TODO deduplicate with PageProperties._deserialize_this()
        property_key_cls = property_registry[typename]
        property_key = property_key_cls(None)
        property_key.id = self.property_id
        # noinspection PyProtectedMember
        property_value = property_key_cls._deserialize_page_value(prop_serialized)
        return property_key, property_value, prop_serialized
