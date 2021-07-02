import os
from pprint import pprint

from notion_client import AsyncClient, Client
from notion_client.api_endpoints import DatabasesEndpoint, PagesEndpoint

from stopwatch import stopwatch
from db_handler.parse import DatabaseParser as DBParser, PageListParser as PLParser
from db_handler.query import QueryHandler

# TODO: .env 파일에 토큰 숨기기
os.environ['NOTION_TOKEN'] = ***REMOVED***
notion = Client(auth=os.environ['NOTION_TOKEN'])

stopwatch('클라이언트 접속')

TEST_PAGE_ID = "5720981faa3e4632846f46f990b6779d"
pprint(notion.blocks.children.list(TEST_PAGE_ID))

stopwatch('작업 완료')
