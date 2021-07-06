from typing import Union

from notion_client import Client, AsyncClient

from interface.requests.edit import PageCreate, PageUpdate, DatabaseCreate, DatabaseUpdate
from interface.requests.query import Query
from interface.parse.databases import DatabasePropertyParser, PageListParser


class NotionWrap:
    def __init__(self, notion: Union[Client, AsyncClient]):
        self.notion = notion

    @classmethod
    def database_query(cls, page_id: str, database_parser=None):
        return Query(page_id, database_parser)

    @classmethod
    def query_response(cls, query_response):
        return PageListParser.from_query(query_response)
