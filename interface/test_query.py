import os
from pprint import pprint
from notion_client import AsyncClient, Client

from stopwatch import stopwatch
from interface.response.parse import PageListParser as PLParser
from interface.requests.query import DatabaseQuery

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
test_db_query_maker = DatabaseQuery(notion, TEST_DATABASE_ID, page_size=30)

name_frame = test_db_query_maker.filter_maker.frame_by_text('이름')
filter1 = name_frame.starts_with('2')
filter2 = name_frame.ends_with('0')
test_filter = (filter1 & filter2)
test_db_query_maker.push_filter(test_filter)
# pprint(test_filter.apply)

test_db_query_maker.sort.append_ascending('이름')
# pprint(test_db_query_maker.sort.apply)

test_subpages = notion.databases.query(**test_db_query_maker.apply())
# pprint(test_subpages)

plain_items = PLParser(test_subpages).list_of_items
pprint(plain_items)

stopwatch('작업 완료')
