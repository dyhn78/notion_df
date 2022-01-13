from typing import Optional

from notion_zap.cli import editors
from notion_zap.cli.utility import stopwatch
from notion_zap.apps.media_scraper.common.struct import (
    ReadingTableController, ReadingPageChecker)
from notion_zap.apps.media_scraper.module_meta.main import MetadataManager
from notion_zap.apps.media_scraper.module_lib import LibraryManager


class RegularScrapController(ReadingTableController):
    LABEL_BKST = {'metadata'}
    LABEL_LIBS = {'gy_lib', 'snu_lib'}

    def __init__(self, tasks: Optional[set] = None, title=''):
        super().__init__()
        if not tasks:
            tasks = self.LABEL_BKST | self.LABEL_LIBS
        self.global_tasks = tasks
        self.title = title
        self.scrap_meta = MetadataManager(self.global_tasks)
        self.scrap_lib = LibraryManager(self.global_tasks)

    def execute(self, request_size=0):
        if not self.fetch(request_size):
            return
        if self.has_lib_tasks(self.global_tasks):
            stopwatch('Selenium 시작..')
            self.scrap_lib.start()
        for page in self.pagelist:
            self.edit(page)
        if self.has_lib_tasks(self.global_tasks):
            stopwatch('Selenium 마감..')
            self.scrap_lib.quit()
            stopwatch('Selenium 종료')

    def fetch(self, request_size):
        query = self.pagelist.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        # maker = manager.checkbox('is_book')
        # ft &= maker.is_not_empty()

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
        checker = RegularReadingPageChecker(page, self.global_tasks)
        tasks = checker.tasks
        if tasks:
            stopwatch(f'개시: {page.title}')
            if 'metadata' in tasks:
                self.scrap_meta(checker)
            if self.has_lib_tasks(tasks):
                self.scrap_lib(checker, tasks)
            checker.mark_as_complete()
            page.save()
        else:
            stopwatch(f'무시: {page.title}')
            return

    @classmethod
    def has_lib_tasks(cls, tasks: set):
        return any(label_lib in tasks for label_lib in cls.LABEL_LIBS)


class RegularReadingPageChecker(ReadingPageChecker):
    def __init__(self, page: editors.PageRow, tasks: set):
        super().__init__(page)
        self.tasks = self.cleaned_tasks(tasks.copy())

    def cleaned_tasks(self, tasks):
        if self._init_label == 'continue':
            tasks.remove('metadata')
        return tasks


if __name__ == '__main__':
    RegularScrapController(tasks={'metadata'}, title='헬스의 정석').execute()
    # RegularScrapController(tasks={'metadata'}).execute(request_size=5)
