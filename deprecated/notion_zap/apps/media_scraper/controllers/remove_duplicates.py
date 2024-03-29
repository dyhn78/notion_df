from notion_zap.cli.utility import stopwatch
from notion_zap.apps.media_scraper.common.media_struct import ReadingTableEditor
from notion_zap.apps.media_scraper.metadata.remove_dummy_blocks import remove_dummy_blocks


class ReadingTableDuplicateRemover(ReadingTableEditor):
    def __init__(self, title=''):
        super().__init__()
        self.title = title

    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.table.rows:
            page.items.fetch()
            if removed := remove_dummy_blocks(page):
                stopwatch(f'중복 {removed} 개 제거: {page.title}')
                page.save()

    def make_query(self, request_size):
        query = self.table.rows.open_query()
        maker = query.filter_manager_by_tags.select('media_type')
        ft_media = maker.equals_to_any(maker.column.key_aliases['book'])
        if self.title:
            maker = query.filter_manager_by_tags.text('title')
            ft_media &= maker.starts_with(self.title)
        query.push_filter(ft_media)
        query.execute(request_size)


if __name__ == '__main__':
    ReadingTableDuplicateRemover().execute(request_size=5)
