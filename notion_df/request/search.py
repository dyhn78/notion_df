from dataclasses import dataclass
from typing import Any, Literal, Union

from notion_df.core.data_base import EntityData
from notion_df.core.request_base import RequestSettings, Version, Method, PaginatedRequestBuilder
from notion_df.data import DatabaseData, PageData
from notion_df.sort import TimestampSort
from notion_df.core.collection import DictFilter


@dataclass
class SearchByTitle(PaginatedRequestBuilder[Union[PageData, DatabaseData]]):
    data_element_type = EntityData
    query: str
    entity: Literal['page', 'database', None] = None
    sort: TimestampSort = TimestampSort('last_edited_time', 'descending')
    page_size: int = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               f'search')

    def get_body(self) -> Any:
        return DictFilter.not_none({
            "query": self.query,
            "filter": ({
                           "value": self.entity,
                           "property": "object"
                       } if self.entity else None),
            "sort": self.sort.serialize()
        })
