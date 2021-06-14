# import json
import os
from stopwatch import stopwatch
from pprint import pprint
from notion_client import AsyncClient, Client, api_endpoints, APIErrorCode, APIResponseError

os.environ['NOTION_TOKEN'] = ***REMOVED***
# notion_async = AsyncClient(auth=NOTION_TOKEN)
notion = Client(auth=os.environ['NOTION_TOKEN'])
stopwatch('클라이언트 접속')


order = 4

if order == 0:
    pprint(notion.users.list())
    stopwatch('유저 목록')

if order == 1:
    "https://www.notion.so/dyhn/NNdev-2106-b65cbbb104a048f99bd07b0ded3d332c"
    TEST_PAGE_ID = "b65cbbb1-04a0-48f9-9bd0-7b0ded3d332c"
    notion.pages.retrieve(page_id=TEST_PAGE_ID)


TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"
if order == 2:
    "https://www.notion.so/dyhn/5c021bea3e2941f39bff902cb2ebfe47?v=161d1c0631fb4b83984bdcb204ad663f"

    test_database = notion.databases.retrieve(**{
            'database_id': TEST_DATABASE_ID,
            'filter': {}
        })
    pprint(test_database)

if order == 4:
    test_subpages = notion.databases.query(database_id=TEST_DATABASE_ID)
    pprint(test_subpages)

if order == 3:
    pprint(os.environ)

stopwatch('작업 완료')

