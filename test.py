from pprint import pprint

from notion_py.interface import RootEditor

root = RootEditor()
page = root.open_inline_page('https://www.notion.so/dyhn/789789-732b5af7bc174e86a60b34cc0c1a3218')
page.contents.retrieve()

# pprint(page.preview())
