import os
from pprint import pprint

from notion_client import AsyncClient, Client
from notion_client.api_endpoints import DatabasesEndpoint, PagesEndpoint

from stopwatch import stopwatch
from db_handler.parser import DatabaseParser as DBParser, PageListParser as PLParser
from db_handler.query_requestor import QueryHandler

# TODO: .env 파일에 토큰 숨기기
os.environ['NOTION_TOKEN'] = ***REMOVED***
notion = Client(auth=os.environ['NOTION_TOKEN'])

stopwatch('클라이언트 접속')

TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"
# test_db = notion.databases.retrieve(database_id=TEST_DATABASE_ID)
notion.pages.create(
                    parent={
                        'database_id': TEST_DATABASE_ID,
                        'type': 'database_id'
                    },
                    properties={
                        'title': [
                                  {
                                    'text': {
                                      'content': 'Tuscan Kale',
                                    },
                                  },
                                ],
                    })

stopwatch('작업 완료')
