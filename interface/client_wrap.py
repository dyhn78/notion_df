from typing import Union

from notion_client import Client, AsyncClient

from requests.edit import PageCreate, PageUpdate, DatabaseCreate, DatabaseUpdate
from requests.query import Query
from parse.databases import DatabasePropertyParser, PageListParser


class NotionWrap:
    def __init__(self, notion: Union[Client, AsyncClient]):
        self.notion = notion

    def database_query(self, page_id: str, page_size: int, database_parser=None, start_cursor=None):
        return Query(self.notion, page_id, page_size, database_parser, start_cursor)

    @classmethod
    def query_response(cls, query_response):
        return PageListParser(query_response)
