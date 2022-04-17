from notion_zap.apps.config import DatabaseInfoDepr
from notion_zap.apps.media_scraper.config import (
    READING_FRAME, STATUS_COLUMN)
from notion_zap.cli import editors
from notion_zap.cli.structs import PropertyMarkedValue


class ReadingTableEditor:
    def __init__(self):
        self.root = editors.Root(print_response_heads=5)
        self.table = self.root.space.database_depr(
            *DatabaseInfoDepr.READINGS, READING_FRAME)


class ReadingPageManager:
    STATUS = STATUS_COLUMN

    def __init__(self, page: editors.PageRow):
        self.page = page
        self._finalized = False
        self._init_value = page.read_key_alias('edit_status')

    @property
    def init_mark(self) -> PropertyMarkedValue:
        return self.STATUS.coalesce_mark(self._init_value, 'default')

    @property
    def success_mark(self):
        return self.STATUS.coalesce_mark(self.init_mark.tags[1])

    @property
    def disable_overwrite(self):
        return 'overwrite' not in self.init_mark.tags

    @property
    def needs_metadata(self):
        return 'metadata' in self.init_mark.tags

    @property
    def needs_location(self):
        return 'location' in self.init_mark.tags

    def mark_exception(self, value_alias):
        if not self._finalized:
            self.page.write_select(key_alias='edit_status', value_alias=value_alias)
            self._finalized = True

    def mark_completion(self):
        if not self._finalized:
            self.page.write_select(key_alias='edit_status',
                                   value=self.success_mark.value)
            self._finalized = True

    @property
    def is_book(self):
        return self.page.read_key_alias('is_book')

    @property
    def titles(self) -> list[str]:
        titles = []
        for key_alias in ['docx_name', 'true_name']:
            if title := self.page.get_key_alias(key_alias):
                titles.append(title)
        return titles
