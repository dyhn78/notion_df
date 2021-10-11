from notion_py.applications.media_scraper.frame import ReadingDB_FRAME
from notion_py.applications.database_info import DatabaseInfo
from notion_py.interface import RootEditor


class ReadingDBEditor:
    def __init__(self):
        self.root_editor = RootEditor()
        self.frame = ReadingDB_FRAME
        self.pagelist = self.root_editor.open_pagelist(
            *DatabaseInfo.READINGS, self.frame)
        self.status_enum = self.frame.by_tag['edit_status'].prop_values
