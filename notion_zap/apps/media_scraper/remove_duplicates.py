from notion_zap.cli.utility import stopwatch
from notion_zap.apps.media_scraper.structs.controller_base_logic import ReadingDBController
from notion_zap.apps.media_scraper.common.remove_dummy_blocks import remove_dummy_blocks


class ReadingDBDuplicateRemover(ReadingDBController):
    def __init__(self, title=''):
        super().__init__()
        self.title = title

    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist:
            page.attachments.fetch()
            if removed := remove_dummy_blocks(page):
                stopwatch(f'중복 {removed} 개 제거: {page.title}')
                page.save()

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.filter_maker.select_at('media_type')
        ft_media = maker.equals_to_any(maker.prop_value_groups['book'])
        if self.title:
            maker = query.filter_maker.text_at('title')
            ft_media &= maker.starts_with(self.title)
        query.push_filter(ft_media)
        query.execute(request_size)


if __name__ == '__main__':
    ReadingDBDuplicateRemover().execute(request_size=5)
