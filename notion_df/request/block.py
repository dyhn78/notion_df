from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from notion_df.request.core import Request, RequestSettings, Version, Method, PaginatedRequest
from notion_df.response.block import ResponseBlock, BlockType
from notion_df.response.misc import UUID
from notion_df.util.collection import DictFilter


@dataclass
class AppendBlockChildren(Request):
    """https://developers.notion.com/reference/patch-block-children"""
    id: UUID
    children: list[BlockType]

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220222, Method.PATCH,
                               f'https://api.notion.com/v1/blocks/{self.id}/children')

    def get_body(self) -> Any:
        return {'children': [{
            "object": "block",
            "type": type_object,
            type_object.get_type(): type_object,
        } for type_object in self.children]}


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
            self.type_object.get_type(): self.type_object,
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
