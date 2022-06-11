from typing import Optional, Iterable

from notion_zap.apps.media_scraper.config import STATUS_COLUMN
from notion_zap.apps.media_scraper.location.main import LibraryScrapManager
from notion_zap.apps.media_scraper.metadata.main import MetadataScrapManager
from notion_zap.apps.media_scraper.struct import (
    ReadingTableEditor, ReadingPageManager)
from notion_zap.cli.editors import PageRow, Database
from notion_zap.cli.utility import stopwatch


class RegularScrapController(ReadingTableEditor):
    LABEL_META = {'metadata'}
    LABEL_LOC = {'gy', 'snu'}

    def __init__(self, targets: Optional[Iterable] = None):
        super().__init__()
        self.fetch = RegularScrapFetcher(self.table)

        if not targets:
            targets = self.LABEL_META | self.LABEL_LOC
        targets = set(targets)
        self.targets_meta = targets & self.LABEL_META
        self.targets_loc = targets & self.LABEL_LOC
        self.get_metadata = MetadataScrapManager(self.targets_meta)
        self.get_location = LibraryScrapManager(self.targets_loc)

    def __call__(self, request_size=0):
        if not self.fetch(request_size):
            stopwatch('읽기: 대상 없음')
            return
        stopwatch('읽기: 시작')
        self.process()

    def process(self):
        for page in self.table.rows:
            self.process_page(page)
        self.get_metadata.quit()
        self.get_location.quit()

    def process_page(self, page: PageRow):
        manager = ReadingPageManager(page)
        stopwatch(f'개시: {page.title}')
        edited = False
        if manager.needs_metadata:
            edited = True
            self.get_metadata(manager)
        if manager.needs_location:
            edited = True
            self.get_location(manager)

        if edited:
            manager.mark_completion()
            page.save()
        else:
            manager.mark_exception('fill_manually')
            stopwatch(f'-- 편집 항목 없음!')


class RegularScrapFetcher:
    def __init__(self, table: Database):
        self.table = table

    def __call__(self, request_size=0, title=''):
        query = self.table.rows.open_query()
        manager = query.filter_manager_by_tags
        ft = query.open_filter()

        # maker = manager.checkbox('is_book')
        # ft &= maker.is_not_empty()

        maker = manager.select('edit_status')
        ft &= (
                maker.equals_to_any(STATUS_COLUMN.filter_values('queue'))
                | maker.is_empty()
        )
        if title:
            maker = manager.text('title')
            ft_title = maker.starts_with(title)
            ft &= ft_title
        query.push_filter(ft)
        pages = query.execute(request_size)
        return pages


if __name__ == '__main__':
    # controller = RegularScrapController(targets={'metadata'})
    # controller.fetch(title='헬스의 정석')
    controller = RegularScrapController()
    controller.fetch(request_size=3)
    controller.process()
    # RegularScrapController(issues={'metadata'}).execute(request_size=5)
