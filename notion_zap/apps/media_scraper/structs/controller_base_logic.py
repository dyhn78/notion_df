import re

from notion_zap.cli import editors
from notion_zap.apps.config import DatabaseInfo
from notion_zap.apps.media_scraper.config import ReadingDB_FRAME


class ReadingDBController:
    status_enum = ReadingDB_FRAME.by_tag['edit_status'].labels

    def __init__(self):
        self.root = editors.Root(print_heads=5)
        self.pagelist = self.root.objects.database(
            *DatabaseInfo.READINGS, ReadingDB_FRAME).rows


class ReadingPageWriter:
    status_enum = ReadingDB_FRAME.by_tag['edit_status'].labels

    def __init__(self, page: editors.PageRow):
        self.page = page
        self._initial_status = self._parse_initial_status()
        self._status = ''

    @property
    def book_names(self) -> list[str]:
        docx_name = self.page.get_tag('docx_name', '')
        true_name = self.page.get_tag('true_name', '')
        return [string for string in (true_name, docx_name) if string]

    def _parse_initial_status(self):
        edit_status = self.page.read_tag('edit_status')
        try:
            charref = re.compile(r'(?<=\().+(?=\))')
            return re.findall(charref, edit_status)[0]
        except (TypeError,  # read() 가 keyError로 edit_status를 반환할 경우
                IndexError):  # findall() 가 빈 리스트를 반환할 경우
            return 'append'

    @property
    def can_disable_overwrite(self):
        return self._initial_status in ['append', 'continue']

    def set_url_missing_flag(self):
        if not self._status:
            self._status = self.status_enum['url_missing']
            self._submit_status()

    def set_lib_missing_flag(self):
        if not self._status:
            self._status = self.status_enum['lib_missing']
            self._submit_status()

    def set_complete_flag(self):
        # TODO: 같은 속성을 가리키는 여러 개의 carrier 를 editor 차원에서 제대로 '덮어쓰기'
        #  할 수 있고 나면, 이 부분은 Controller 가 더 이상 명시적으로 호출하지 않아도
        #  되어야 한다.
        if not self._status:
            if self._initial_status == 'append':
                self._status = self.status_enum['tentatively_done']
            elif self._initial_status == 'continue':
                self._status = self.status_enum['tentatively_done']
            elif self._initial_status == 'overwrite':
                self._status = self.status_enum['completely_done']
            else:
                raise ValueError(f"{self._status=}")
            self._submit_status()

    def _submit_status(self):
        self.page.write_select(tag='edit_status', value=self._status)
