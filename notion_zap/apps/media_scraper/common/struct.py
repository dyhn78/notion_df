from notion_zap.cli import editors
from notion_zap.apps.config.common import DatabaseInfo
from notion_zap.apps.config.media_scraper import ReadingDB_FRAME


class ReadingDBController:
    def __init__(self):
        self.root = editors.RootEditor()
        self.pagelist = self.root.open_database(
            *DatabaseInfo.READINGS, ReadingDB_FRAME).pages
        self.status_enum = ReadingDB_FRAME.by_tag['edit_status'].prop_values


class ReadingPageManager:
    def __init__(self, caller: ReadingDBController, page: editors.PageRow):
        self.caller = caller
        self.page = page
        self.root = page.root
        self.status_enum = ReadingDB_FRAME.by_tag['edit_status'].prop_values
