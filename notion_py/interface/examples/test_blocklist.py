import os
from pprint import pprint

from notion_client import Client

from notion_py.helpers.stopwatch import stopwatch

os.environ['NOTION_TOKEN'] = ***REMOVED***
notion = Client(auth=os.environ['NOTION_TOKEN'])

stopwatch('클라이언트 접속')

TEST_PAGE_ID = "5720981faa3e4632846f46f990b6779d"
pprint(notion.pages.retrieve(TEST_PAGE_ID))
print('\n'*3)
pprint(notion.blocks.children.list(TEST_PAGE_ID))

stopwatch('작업 완료')
