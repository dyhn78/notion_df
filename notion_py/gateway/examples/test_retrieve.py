from notion_client import Client
from pprint import pprint

notion = Client(auth=***REMOVED***)
pprint(notion.pages.retrieve(page_id='cc794772ba904c528c06bafd24a613f0'))