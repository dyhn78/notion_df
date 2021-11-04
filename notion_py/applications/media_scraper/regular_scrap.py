import re
from typing import Optional

from notion_py.interface.editor.tabular import PageRow
from notion_py.interface.utility import stopwatch
from .common.struct import ReadingDBController, ReadingPageController


class ReadingDBScrapController(ReadingDBController):
    def __init__(self, tasks: Optional[set] = None, title=''):
        super().__init__()
        if not tasks:
            tasks = {'bookstore', 'gy_lib', 'snu_lib'}
        self.tasks = tasks
        self.title = title

        from .bookstore import BookstoreScrapManager
        self.bkst = BookstoreScrapManager(self)

        from .lib import LibraryScrapManager
        self.lib = LibraryScrapManager(self)

    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist:
            unit = ReadingPageScrapController(self, page)
            unit.execute()

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.filter_maker.select_at('media_type')
        ft_media = maker.equals_to_any(maker.prop_value_groups['book'])
        maker = query.filter_maker.select_at('edit_status')
        ft_status = maker.equals_to_any(maker.prop_value_groups['regulars'])
        ft_status |= maker.is_empty()
        ft = ft_media & ft_status
        if self.title:
            maker = query.filter_maker.text_at('title')
            ft_title = maker.starts_with(self.title)
            ft &= ft_title
        query.push_filter(ft)
        query.execute(request_size)


class ReadingPageScrapController(ReadingPageController):
    def __init__(self, caller: ReadingDBScrapController, page: PageRow):
        super().__init__(caller, page)
        self.caller = caller
        self.page = page
        self.rich_overwrite_option = self.get_overwrite_option()

        self.tasks = caller.tasks.copy()
        if self.rich_overwrite_option == 'continue':
            self.tasks.remove('bookstore')
        self._status = ''
        self._status_finalized = False

    def execute(self):
        if not self.tasks:
            return
        stopwatch(f'개시: {self.page.title}')
        if 'bookstore' in self.tasks:
            self.caller.bkst.execute(self)
        if any(lib_str in self.tasks for lib_str in ['snu_lib', 'gy_lib']):
            self.caller.lib.execute(self)
        if not self._status:
            self.set_as_done()
        self.page.props.write_select_at('edit_status', self._status)
        self.page.save()

    def get_names(self) -> tuple[str, str]:
        docx_name = self.page.props.get_at('docx_name', '')
        true_name = self.page.props.get_at('true_name', '')
        return docx_name, true_name

    @property
    def can_disable_overwrite(self):
        if self.rich_overwrite_option in ['append', 'continue']:
            return True
        elif self.rich_overwrite_option == ['overwrite']:
            return False

    def get_overwrite_option(self):
        edit_status = self.page.props.read_at('edit_status')
        try:
            charref = re.compile(r'(?<=\().+(?=\))')
            return re.findall(charref, edit_status)[0]
        except (TypeError,  # read() 가 keyError로 edit_status를 반환할 경우
                IndexError):  # findall() 가 빈 리스트를 반환할 경우
            return 'append'

    def set_as_url_missing(self):
        if self._status_finalized:
            return
        self._status = self.caller.status_enum['url_missing']
        self._status_finalized = True

    def set_as_lib_missing(self):
        if self._status_finalized:
            return
        self._status = self.caller.status_enum['lib_missing']
        self._status_finalized = True

    def set_as_done(self):
        if self.rich_overwrite_option == 'append':
            self._status = self.caller.status_enum['done']
        elif self.rich_overwrite_option == 'continue':
            self._status = self.caller.status_enum['done']
        elif self.rich_overwrite_option == 'overwrite':
            self._status = self.caller.status_enum['completely_done']
