from notion_zap.interface import editor
from .common.struct import ReadingDBController


class ReadingDBStatusResolver(ReadingDBController):
    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist:
            self.edit(page)

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.filter_maker.select_at('media_type')
        ft = maker.equals_to_any(maker.prop_value_groups['book'])
        maker = query.filter_maker.select_at('edit_status')
        ft &= maker.equals_to_any(maker.prop_value_groups['need_resets'])
        """
        maker = query.filter_maker.checkbox_at('not_available')
        ft |= maker.equals(True)
        """
        query.push_filter(ft)
        query.execute(request_size)

    def edit(self, page: editor.PageRow):
        page.props.write_select_at('edit_status', self.status_enum['append'])
        page.props.write_checkbox_at('not_available', False)
        page.save()
