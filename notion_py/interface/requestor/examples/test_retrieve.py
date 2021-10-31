from pprint import pprint

from notion_client import Client

notion = Client(auth=***REMOVED***)
pprint(notion.pages.retrieve())
