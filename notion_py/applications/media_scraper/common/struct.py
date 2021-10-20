from notion_py.applications.media_scraper.frame import ReadingDB_FRAME
from notion_py.applications.database_info import DatabaseInfo
from notion_py.interface import RootEditor
from notion_py.interface.editor.tabular import TabularPageBlock


class ReadingDBController:
    def __init__(self):
        self.root = RootEditor()
        self.pagelist = self.root.open_pagelist(
            *DatabaseInfo.READINGS, ReadingDB_FRAME)
        self.status_enum = ReadingDB_FRAME.by_tag['edit_status'].prop_values


class ReadingPageController:
    def __init__(self, caller: ReadingDBController, page: TabularPageBlock):
        self.caller = caller
        self.page = page
        self.root = page.root
