from typing import Optional

from notion_zap.cli import editors
from notion_zap.cli.utility import stopwatch
from notion_zap.apps.media_scraper.structs.controller_base_logic import (
    ReadingDBController, ReadingPageWriter)
from notion_zap.apps.media_scraper.module_bkst.main import BookstoreDataWriter
from notion_zap.apps.media_scraper.module_lib import LibraryManager


class RegularScrapController(ReadingDBController):
    TASKS_BKST = {'bookstore'}
    TASKS_LIBS = {'gy_lib', 'snu_lib'}
    BKST = BookstoreDataWriter

    def __init__(self, tasks: Optional[set] = None, title=''):
        super().__init__()
        if not tasks:
            tasks = self.TASKS_BKST | self.TASKS_LIBS
        self.global_tasks = tasks
        self.title = title
        self.lib = LibraryManager(self.global_tasks)
        self.has_lib_tasks = any(lib in self.global_tasks for lib in self.TASKS_LIBS)

    def execute(self, request_size=0):
        if not self.fetch(request_size):
            return
        if self.has_lib_tasks:
            stopwatch('Selenium 시작..')
            self.lib.start()
        for page in self.pagelist:
            self.edit(page)
        if self.has_lib_tasks:
            stopwatch('Selenium 마감..')
            self.lib.quit()
            stopwatch('Selenium 종료')

    def fetch(self, request_size):
        query = self.pagelist.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        maker = manager.checkbox('is_book')
        ft &= maker.is_not_empty()

        maker = manager.select('edit_status')
        ft &= (
                maker.equals_to_any(maker.column.marks['regular_scraps'])
                | maker.is_empty()
        )
        if self.title:
            maker = manager.text('title')
            ft_title = maker.starts_with(self.title)
            ft &= ft_title
        query.push_filter(ft)
        pages = query.execute(request_size)
        return pages

    def edit(self, page: editors.PageRow):
        status = ReadingPageStatusWriter(page, self.global_tasks.copy())
        if status.tasks:
            stopwatch(f'개시: {page.title}')
            if 'bookstore' in status.tasks:
                if not self.BKST(status).execute():
                    status.set_url_missing_flag()
            if any(lib_str in status.tasks for lib_str in ['snu_lib', 'gy_lib']):
                if not self.lib.execute(status, status.tasks):
                    status.set_lib_missing_flag()
            status.set_complete_flag()
            page.save()
        else:
            stopwatch(f'무시: {page.title}')
            return


class ReadingPageStatusWriter(ReadingPageWriter):
    def __init__(self, page: editors.PageRow, tasks: set):
        super().__init__(page)
        self.tasks = tasks
        if self._initial_status == 'continue':
            self.tasks.remove('bookstore')


if __name__ == '__main__':
    RegularScrapController(tasks={'bookstore'}).execute(request_size=5)
