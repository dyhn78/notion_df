from notion_zap.interface import editor
from notion_zap.applications.config.common import DatabaseInfo
from notion_zap.applications.config.media_scraper import ReadingDB_FRAME


class ReadingDBController:
    def __init__(self):
        self.root = editor.RootEditor()
        self.pagelist = self.root.open_database(
            *DatabaseInfo.READINGS, ReadingDB_FRAME).pagelist
        self.status_enum = ReadingDB_FRAME.by_tag['edit_status'].prop_values


class ReadingPageController:
    def __init__(self, caller: ReadingDBController, page: editor.PageRow):
        self.caller = caller
        self.page = page
        self.root = page.root
