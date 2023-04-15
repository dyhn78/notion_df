from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

from notion_df.object.block import BlockType, type_object_registry
from notion_df.object.core import Deserializable
from notion_df.object.misc import UUID
from notion_df.object.parent import Parent
from notion_df.object.user import User
from notion_df.request.core import Request, RequestSettings, Version, Method, PaginatedRequest
from notion_df.request.page import serialize_partial_block_list
from notion_df.util.collection import DictFilter


@dataclass
class ResponseBlock(Deserializable):
    id: UUID
    parent: Parent
    created_time: datetime
    last_edited_time: datetime
    created_by: User
    last_edited_by: User
    has_children: bool
    archived: bool
    type_object: BlockType

    @classmethod
    def deserialize(cls, response_data: dict[str, Any]):
        typename = response_data['type']
        type_object_cls = type_object_registry[typename]
        type_object = type_object_cls.deserialize(response_data[typename])
        return cls._deserialize_asdict(response_data | {'type_object': type_object})


@dataclass
class AppendBlockChildren(Request[list[ResponseBlock]]):
    """https://developers.notion.com/reference/patch-block-children"""
    id: UUID
    children: list[BlockType]

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'https://api.notion.com/v1/blocks/{self.id}/children')

    def get_body(self) -> Any:
        return {'children': serialize_partial_block_list(self.children)}

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> list[ResponseBlock]:
        data_element_list = []
        for data_element in data['results']:
            data_element_list.append(ResponseBlock.deserialize(data_element))
        return data_element_list


@dataclass
class RetrieveBlock(Request[ResponseBlock]):
    """https://developers.notion.com/reference/retrieve-a-block"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.GET,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class RetrieveBlockChildren(PaginatedRequest[ResponseBlock]):
    """https://developers.notion.com/reference/get-block-children"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.GET,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self) -> Any:
        pass


@dataclass
class UpdateBlock(Request[ResponseBlock]):
    """https://developers.notion.com/reference/update-a-block"""
    id: UUID
    type_object: BlockType = field(default=None)
    archived: bool = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self):
        return DictFilter.not_none({
            'block_id': self.id,
            self.type_object.get_typename(): self.type_object,
            'archived': self.archived
        })


@dataclass
class DeleteBlock(Request[ResponseBlock]):
    """https://developers.notion.com/reference/delete-a-block"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.DELETE,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self) -> Any:
        return
