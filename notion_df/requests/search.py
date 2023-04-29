from dataclasses import dataclass
from typing import Any, Literal, Union

from notion_df.objects.database import ResponseDatabase
from notion_df.objects.page import ResponsePage
from notion_df.objects.sort import TimestampSort
from notion_df.requests.core import RequestSettings, Version, Method, PaginatedRequest
from notion_df.utils.collection import DictFilter


@dataclass
class SearchByTitle(PaginatedRequest[Union[ResponsePage, ResponseDatabase]]):
    query: str
    filter: Literal['page', 'database', None] = None
    sort: TimestampSort = TimestampSort('last_edited_time', 'descending')

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/search')

    def get_body(self) -> Any:
        return DictFilter.not_none({
            "query": self.query,
            "filter": self.filter,
            "sort": self.sort
        })
