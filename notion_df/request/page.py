from dataclasses import dataclass, field
from typing import Any

from notion_df.request.core import Request, RequestSettings, Version, Method
from notion_df.response.block import BlockObject
from notion_df.response.file import ExternalFile
from notion_df.response.misc import UUID, Icon
from notion_df.response.page import ResponsePage, PageProperty, BaseResponsePageProperty
from notion_df.response.parent import Parent


@dataclass
class RetrievePage(Request[ResponsePage]):
    """https://developers.notion.com/reference/retrieve-a-database"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/databases/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class CreatePage(Request[ResponsePage]):
    """https://developers.notion.com/reference/create-a-database"""
    parent: Parent
    icon: Icon
    cover: ExternalFile
    properties: dict[str, PageProperty] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    children: list[BlockObject] = field()

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/pages')

    def get_body(self) -> Any:
        return {
            "parent": self.parent,
            "icon": self.icon,
            "cover": self.cover,
            "properties": self.properties,
            "children": self.children,
        }


@dataclass
class UpdatePage(Request[ResponsePage]):
    """https://developers.notion.com/reference/update-a-database"""
    id: UUID
    icon: Icon
    cover: ExternalFile
    properties: dict[str, PageProperty] = field()
    """the dict keys are same as each property's name or id (depending on request)"""
    archived: bool

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.PATCH,
                               f'https://api.notion.com/v1/pages/{self.id}')

    def get_body(self) -> Any:
        return {
            "icon": self.icon,
            "cover": self.cover,
            "properties": self.properties,
            "archived": self.archived,
        }


@dataclass
class RetrievePageProperty(Request[BaseResponsePageProperty]):
    """https://developers.notion.com/reference/retrieve-a-page-property"""
    page_id: UUID
    property_id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.GET,
                               f'https://api.notion.com/v1/pages/{self.page_id}/properties/{self.property_id}')

    def get_body(self) -> Any:
        return
