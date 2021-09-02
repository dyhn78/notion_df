from notion_client import Client

notion = Client(None)

TEST_DATABASE_ID = "5c021bea3e2941f39bff902cb2ebfe47"
notion.pages.create()
