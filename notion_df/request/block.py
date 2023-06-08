from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from notion_df.object.block import BlockValue, BlockResponse, serialize_block_value_list
from notion_df.core.request import SingleRequest, RequestSettings, Version, Method, PaginatedRequest
from notion_df.util.collection import DictFilter


@dataclass
class AppendBlockChildren(SingleRequest[list[BlockResponse]]):
    """https://developers.notion.com/reference/patch-block-children"""
    response_type = list[BlockResponse]
    id: UUID
    children: list[BlockValue]

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'https://api.notion.com/v1/blocks/{self.id}/children')

    def get_body(self) -> Any:
        return {'children': serialize_block_value_list(self.children)}

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> list[BlockResponse]:
        data_element_list = []
        for data_element in data['results']:
            data_element_list.append(BlockResponse.deserialize(data_element))
        return data_element_list


@dataclass
class RetrieveBlock(SingleRequest[BlockResponse]):
    """https://developers.notion.com/reference/retrieve-a-block"""
    response_type = BlockResponse
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.GET,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class RetrieveBlockChildren(PaginatedRequest[BlockResponse]):
    """https://developers.notion.com/reference/get-block-children"""
    response_element_type = BlockResponse
    id: UUID
    page_size: int = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.GET,
                               f'https://api.notion.com/v1/blocks/{self.id}/children')

    def get_body(self) -> Any:
        pass


@dataclass
class UpdateBlock(SingleRequest[BlockResponse]):
    """https://developers.notion.com/reference/update-a-block"""
    response_type = BlockResponse
    id: UUID
    block_type: BlockValue = field(default=None)
    archived: bool = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self):
        return DictFilter.not_none({
            'block_id': self.id,
            self.block_type.get_typename(): self.block_type,
            'archived': self.archived
        })


@dataclass
class DeleteBlock(SingleRequest[BlockResponse]):
    """https://developers.notion.com/reference/delete-a-block"""
    response_type = BlockResponse
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.DELETE,
                               f'https://api.notion.com/v1/blocks/{self.id}')

    def get_body(self) -> Any:
        return
