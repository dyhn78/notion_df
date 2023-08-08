from dataclasses import dataclass
from typing import Any, Literal, Union

from notion_df.core.request import RequestSettings, Version, Method, PaginatedRequestBuilder, Response
from notion_df.object.block import DatabaseResponse, PageResponse
from notion_df.object.sort import TimestampSort
from notion_df.util.collection import DictFilter


@dataclass
class SearchByTitle(PaginatedRequestBuilder[Union[PageResponse, DatabaseResponse]]):
    response_element_type = Response
    query: str
    entity: Literal['page', 'database', None] = None
    sort: TimestampSort = TimestampSort('last_edited_time', 'descending')
    page_size: int = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'https://api.notion.com/v1/search')

    def get_body(self) -> Any:
        return DictFilter.not_none({
            "query": self.query,
            "filter": ({
                           "value": self.entity,
                           "property": "object"
                       } if self.entity else None),
            "sort": self.sort
        })
