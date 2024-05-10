from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any
from uuid import UUID

from notion_df.contents import BlockContents, serialize_block_contents_list
from notion_df.core.request import SingleRequestBuilder, RequestSettings, Version, Method, PaginatedRequestBuilder
from notion_df.object.data import BlockData
from notion_df.util.collection import DictFilter


@dataclass
class AppendBlockChildren(SingleRequestBuilder[list[BlockData]]):
    """https://developers.notion.com/reference/patch-block-children"""
    data_type = list[BlockData]
    id: UUID
    children: list[BlockContents]

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'blocks/{self.id}/children')

    def get_body(self) -> Any:
        return {'children': serialize_block_contents_list(self.children)}

    @classmethod
    def parse_response_data(cls, data: dict[str, Any]) -> list[BlockData]:
        data_element_list = []
        for data_element in data['results']:
            data_element_list.append(BlockData.deserialize(data_element))
        return data_element_list


@dataclass
class RetrieveBlock(SingleRequestBuilder[BlockData]):
    """https://developers.notion.com/reference/retrieve-a-block"""
    data_type = BlockData
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.GET,
                               f'blocks/{self.id}')

    def get_body(self) -> Any:
        return


@dataclass
class RetrieveBlockChildren(PaginatedRequestBuilder[BlockData]):
    """https://developers.notion.com/reference/get-block-children"""
    data_element_type = BlockData
    id: UUID
    page_size: int = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.GET,
                               f'blocks/{self.id}/children')

    def get_body(self) -> Any:
        pass


@dataclass
class UpdateBlock(SingleRequestBuilder[BlockData]):
    """https://developers.notion.com/reference/update-a-block"""
    data_type = BlockData
    id: UUID
    block_type: BlockContents = field(default=None)
    archived: bool = field(default=None)

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'blocks/{self.id}')

    def get_body(self):
        return DictFilter.not_none({
            'block_id': str(self.id),
            self.block_type.get_typename(): self.block_type.serialize(),
            'archived': self.archived
        })


@dataclass
class DeleteBlock(SingleRequestBuilder[BlockData]):
    """https://developers.notion.com/reference/delete-a-block"""
    data_type = BlockData
    id: UUID

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.DELETE,
                               f'blocks/{self.id}')

    def get_body(self) -> Any:
        return
