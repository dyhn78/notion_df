from notion_py.interface import RootEditor

root = RootEditor()
page = root.open_inline_page('56ce1823-d086-4a05-a85f-88e47ece7f72')
"""block = page.sphere.create_text_block()
block.contents.write_to_do('some_text', True)"""
subpage = page.sphere.create_inline_page()
subpage.contents.write_title('xyz')
page.execute()
