from notion_client import Client
from pprint import pprint

notion = Client(auth=***REMOVED***)
pprint(notion.pages.retrieve_this())
