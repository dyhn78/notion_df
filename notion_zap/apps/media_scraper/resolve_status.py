from notion_zap.cli import editors
from notion_zap.apps.media_scraper.structs.controller_base_logic import ReadingDBController


class ReadingDBStatusResolver(ReadingDBController):
    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist:
            self.edit(page)

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.filter_manager_by_tags.select('media_type')
        ft = maker.equals_to_any(maker.column.marks['book'])
        maker = query.filter_manager_by_tags.select('edit_status')
        ft &= maker.equals_to_any(maker.column.marks['need_resets'])
        """
        maker = query.filter_manager_by_tags.checkbox_at('not_available')
        ft |= maker.equals(True)
        """
        query.push_filter(ft)
        query.execute(request_size)

    def edit(self, page: editors.PageRow):
        property_writer = page.props
        value = self.status_enum['append']
        property_writer.write_select(tag='edit_status', value=value)
        writer = page.props
        writer.write_checkbox(tag='not_available', value=False)
        page.save()


if __name__ == '__main__':
    ReadingDBStatusResolver().execute(request_size=5)
