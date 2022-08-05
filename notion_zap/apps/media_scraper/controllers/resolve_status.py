from notion_zap.apps.media_scraper.config import READING_FRAME
from notion_zap.apps.media_scraper.struct import ReadingTableEditor
from notion_zap.cli import blocks


class ReadingTableStatusResolver(ReadingTableEditor):
    status_enum = READING_FRAME.by_alias['edit_status'].marks

    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.table.rows:
            self.edit(page)

    def make_query(self, request_size):
        query = self.table.rows.open_query()
        maker = query.filter_manager_by_tags.select('media_type')
        ft = maker.equals_to_any(maker.column.key_aliases['book'])
        maker = query.filter_manager_by_tags.select('edit_status')
        ft &= maker.equals_to_any(maker.column.key_aliases['need_resets'])
        """
        maker = query.filter_manager_by_tags.checkbox_at('not_available')
        ft |= maker.equals(True)
        """
        query.push_filter(ft)
        query.execute(request_size)

    def edit(self, page: blocks.PageRow):
        value = self.status_enum['append']
        page.write_select(key_alias='edit_status', value=value)
        page.write_checkbox(key_alias='not_available', value=False)
        page.save()


if __name__ == '__main__':
    ReadingTableStatusResolver().execute(request_size=5)
