from notion_zap.cli import editors
from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.media_scraper.config import READING_FRAME


class ReadingTableEditor:
    def __init__(self):
        self.root = editors.Root(print_response_heads=5)
        self.table = self.root.objects.database(
            *DatabaseInfo.READINGS, READING_FRAME)


class ReadingPageEditor:
    STATUS_CL = READING_FRAME.by_tag['edit_status']
    STATUS_LABELS = STATUS_CL.labels
    TERMINAL_LABELS = {'append': 'tentatively_done',
                       'overwrite': 'completely_done',
                       'continue': 'tentatively_done'}

    def __init__(self, page: editors.PageRow):
        self.page = page
        self._init_value = page.read_tag('edit_status')
        self._init_label = self.STATUS_CL.label_of(self._init_value, 'append')
        self._init_marks = self.STATUS_CL.marks_of(self._init_value)
        self._terminal = self.TERMINAL_LABELS[self._init_label]
        self._finalized = False
        self._status = ''

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

    @property
    def cannot_overwrite_metadata(self):
        return 'cannot_overwrite' in self._init_marks

    @property
    def must_clear_previous_contents(self):
        return self._init_label == 'overwrite'

    def mark_as_url_missing(self):
        self.write('url_missing')

    def mark_as_lib_missing(self):
        self.write('lib_missing')

    def mark_as_manually_filled(self):
        self.write('manually_filled')

    def mark_as_complete(self):
        self.write(self._terminal)

    def write(self, label):
        if not self._finalized:
            self.page.write_select(tag='edit_status', label=label)
            self._finalized = True

    def needs_to_scrap_metadata(self):
        return self._init_label != 'continue'
