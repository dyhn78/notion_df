from dataclasses import dataclass
from typing import Any, Literal, Union

from notion_df.core.data import Data
from notion_df.core.request import RequestSettings, Version, Method, PaginatedRequestBuilder
from notion_df.object.data import DatabaseData, PageData
from notion_df.object.sort import TimestampSort
from notion_df.util.collection import DictFilter


@dataclass
class SearchByTitle(PaginatedRequestBuilder[Union[PageData, DatabaseData]]):
    data_element_type = Data
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
            "sort": self.sort.serialize()
        })
