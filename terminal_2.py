from notion_py.interface import RootEditor

root = RootEditor()
page = root.open_inline_page('56ce1823-d086-4a05-a85f-88e47ece7f72')
subpage = page.pagelist.create_inline_page()
subpage.contents.write_title('xyz')
subpage.execute()

