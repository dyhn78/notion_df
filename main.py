import os
from pprint import pprint
from notion_client import AsyncClient, Client
# from notion_client import api_endpoints, APIErrorCode, APIResponseError

from stopwatch import stopwatch
from db_handler.parser import DatabaseParser as DBRetrieveReader, PagesParser as DBQueryReader
from db_handler.query_handler import QueryHandler

# TODO: .env 파일에 토큰 숨기기
os.environ['NOTION_TOKEN'] = ***REMOVED***
notion = Client(auth=os.environ['NOTION_TOKEN'])

stopwatch('클라이언트 접속')

stopwatch('작업 완료')
