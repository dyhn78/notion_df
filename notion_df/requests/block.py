from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from notion_df.objects.block import BlockType, ResponseBlock
from notion_df.objects.misc import UUID
from notion_df.requests.common import serialize_partial_block_list
from notion_df.requests.core import SingleRequest, RequestSettings, Version, Method, PaginatedRequest
from notion_df.utils.collection import DictFilter


@dataclass
class AppendBlockChildren(SingleRequest[list[ResponseBlock]]):
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
class RetrieveBlock(SingleRequest[ResponseBlock]):
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
class UpdateBlock(SingleRequest[ResponseBlock]):
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
class DeleteBlock(SingleRequest[ResponseBlock]):
    """https://developers.notion.com/reference/delete-a-block"""
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.DELETE,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self) -> Any:
        return
