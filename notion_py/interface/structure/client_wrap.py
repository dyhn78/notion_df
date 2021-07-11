from typing import Union

from notion_client import Client, AsyncClient

from notion_py.interface.requests.query import Query
from client_wrap.parse.databases import PageListParser


class NotionWrap:
    def __init__(self, notion: Union[Client, AsyncClient]):
        self.notion = notion

    @classmethod
    def database_query(cls, page_id: str, database_parser=None):
        return Query(page_id, database_parser)

    @classmethod
    def query_response(cls, query_response):
        return PageListParser.from_query(query_response)
