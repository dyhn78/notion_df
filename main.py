import os
from pprint import pprint
from notion_client import AsyncClient, Client
# from notion_client import api_endpoints, APIErrorCode, APIResponseError

from stopwatch import stopwatch
from helpers import flatten_query

# TODO .env파일에 토큰 숨기기
os.environ['NOTION_TOKEN'] = ***REMOVED***

ASYNC = False

if ASYNC:
    notion = AsyncClient(auth=os.environ['NOTION_TOKEN'])
else:
    notion = Client(auth=os.environ['NOTION_TOKEN'])

stopwatch('클라이언트 접속')

TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"

for i in range(10):
    test_subpages = notion.databases.query(**{
        'database_id': TEST_DATABASE_ID,
        'filter': {
            'or': [{
                'property': '이름',
                'text': {'contains': '1'}
                },
                {
                'property': '이름',
                'text': {'contains': '1'}
            }]
        }
    })

    flatten_query(test_subpages)
# pprint(flatten_query(test_subpages))

# help(notion.databases)

stopwatch('작업 완료')




