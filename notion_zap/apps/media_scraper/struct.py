from notion_zap.cli import editors
from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.media_scraper.config import (
    READING_FRAME, STATUS_COLUMN)
from notion_zap.cli.structs import PropertyMarkedValue


class ReadingTableEditor:
    def __init__(self):
        self.root = editors.Root(print_response_heads=5)
        self.table = self.root.objects.database(
            *DatabaseInfo.READINGS, READING_FRAME)


class ReadingPageManager:
    STATUS = STATUS_COLUMN

    def __init__(self, page: editors.PageRow):
        self.page = page
        self._finalized = False
        self._init_value = page.read_tag('edit_status')

    @property
    def init_mark(self) -> PropertyMarkedValue:
        return self.STATUS.get_mark(self._init_value, self.STATUS.marks['default'])

    @property
    def success_label(self):
        return self.STATUS.get_mark(self.init_mark.tags[1])

    @property
    def enable_overwrite(self):
        return 'overwrite' in self.init_mark.tags

    @property
    def needs_metadata(self):
        return 'metadata' in self.init_mark.tags

    @property
    def needs_location(self):
        return 'location' in self.init_mark.tags

    def mark_exception(self, label):
        if not self._finalized:
            self.page.write_select(key_alias='edit_status', value_alias=label)
            self._finalized = True

    def mark_completion(self):
        if not self._finalized:
            self.page.write_select(key_alias='edit_status',
                                   value_alias=self.success_label)
            self._finalized = True

    @property
    def is_book(self):
        return self.page.read_tag('is_book')

    @property
    def titles(self) -> list[str]:
        titles = []
        for key_alias in ['docx_name', 'true_name']:
            if title := self.page.get_tag(key_alias):
                titles.append(title)
        return titles
