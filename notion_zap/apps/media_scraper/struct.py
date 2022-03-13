from notion_zap.cli import editors
from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.media_scraper.config import (
    READING_FRAME, STATUSES, STATUS_DEFAULT)


class ReadingTableEditor:
    def __init__(self):
        self.root = editors.Root(print_response_heads=5)
        self.table = self.root.objects.database(
            *DatabaseInfo.READINGS, READING_FRAME)


class ReadingPageEditor:
    STATUS = STATUSES
    STATUS_LABELS = STATUS.labels

    def __init__(self, page: editors.PageRow):
        self.page = page
        self._init_value = page.read_tag('edit_status')
        self._finalized = False

    @property
    def init_label(self):
        return self.STATUS.label_of(
            self._init_value, STATUS_DEFAULT)

    @property
    def complete_label(self):
        return 'success', self.init_label[-1]

    @property
    def enable_overwrite(self):
        return 'overwrite' in self.init_label

    @property
    def needs_metadata(self):
        return 'metadata' in self.init_label

    @property
    def needs_location(self):
        return 'location' in self.init_label

    def mark_exception(self, label):
        if not self._finalized:
            self.page.write_select(tag='edit_status', label=label)
            self._finalized = True

    def mark_completion(self):
        if not self._finalized:
            self.page.write_select(tag='edit_status', label=self.complete_label)
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
