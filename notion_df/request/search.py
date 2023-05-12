from dataclasses import dataclass
from typing import Any, Literal, Union

from notion_df.object.block import DatabaseResponse, PageResponse
from notion_df.object.sort import TimestampSort
from notion_df.request.request_core import RequestSettings, Version, Method, PaginatedRequest
from notion_df.util.collection import DictFilter


@dataclass
class SearchByTitle(PaginatedRequest[Union[PageResponse, DatabaseResponse]]):
    return_type = Union[PageResponse, DatabaseResponse]
    query: str
    filter: Literal['page', 'database', None] = None
    sort: TimestampSort = TimestampSort('last_edited_time', 'descending')
    page_size: int = -1

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/search')

    def get_body(self) -> Any:
        return DictFilter.not_none({
            "query": self.query,
            "filter": self.filter,
            "sort": self.sort
        })
