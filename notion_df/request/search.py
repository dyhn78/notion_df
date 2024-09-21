from dataclasses import dataclass
from typing import Any, Literal, Union

from notion_df.core.collection import DictFilter
from notion_df.core.data_core import EntityData
from notion_df.core.request_core import RequestSettings, Version, Method, PaginatedRequestBuilder
from notion_df.data import DatabaseData, PageData
from notion_df.sort import TimestampSort


@dataclass
class SearchByTitle(PaginatedRequestBuilder[Union[PageData, DatabaseData]]):
    data_element_type = EntityData
    query: str
    entity: Literal['page', 'database', None] = None
    sort: TimestampSort = TimestampSort('last_edited_time', 'descending')
    page_size: int | None = None

    def get_settings(self) -> RequestSettings:
        return RequestSettings(Version.v20220628, Method.POST,
                               'search')

    def get_body(self) -> Any:
        return DictFilter.not_none({
            "query": self.query,
            "filter": ({
                           "value": self.entity,
                           "property": "object"
                       } if self.entity else None),
            "sort": self.sort.serialize()
        })
