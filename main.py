import os
from pprint import pprint
from notion_client import AsyncClient, Client
# from notion_client import api_endpoints, APIErrorCode, APIResponseError

from stopwatch import stopwatch
from db_reader import DatabaseRetrieveReader as DBRetrieveReader, DatabaseQueryReader as DBQueryReader
from db_query.filter_maker import QueryFrameMaker, AndFilter as And, OrFilter as Or

# TODO: .env 파일에 토큰 숨기기
os.environ['NOTION_TOKEN'] = ***REMOVED***

ASYNC = False

if ASYNC:
    notion = AsyncClient(auth=os.environ['NOTION_TOKEN'])
else:
    notion = Client(auth=os.environ['NOTION_TOKEN'])

stopwatch('클라이언트 접속')

TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"

test_database = notion.databases.retrieve(database_id=TEST_DATABASE_ID)
test_retrieve_reader = DBRetrieveReader(test_database)

default_filter = {'database_id': TEST_DATABASE_ID,
                  'filter': {
                      'and': [{
                          'property': '이름',
                          'text': {'starts_with': '2'}
                      },
                          {
                              'property': '이름',
                              'text': {'ends_with': '0'}
                          }]
                  }}

testdb_frame = QueryFrameMaker(test_retrieve_reader)
name_frame = testdb_frame.text('이름')
filter1 = name_frame.starts_with('2')
filter2 = name_frame.ends_with('0')
test_filter = And(filter1, filter2)

pprint(test_filter.apply)
pprint(test_filter.nesting)

test_subpages = notion.databases.query(database_id=TEST_DATABASE_ID, filter=test_filter.apply)

print('\n' * 3)
pprint(DBQueryReader(test_subpages).plain_items)

# help(notion.databases)

stopwatch('작업 완료')
