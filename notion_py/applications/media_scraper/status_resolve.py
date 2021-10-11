from .common.editor import ReadingDBEditor
from notion_py.interface import TypeName


class ReadingDBStatusResolver(ReadingDBEditor):
    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist.elements:
            self.edit(page)

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.make_filter.select_at('media_type')
        ft = maker.equals_to_any(maker.prop_value_groups['book'])
        maker = query.make_filter.select_at('edit_status')
        ft &= maker.equals_to_any(maker.prop_value_groups['need_resets'])
        """
        maker = query.make_filter.checkbox_at('not_available')
        ft |= maker.equals(True)
        """
        query.push_filter(ft)
        query.execute(request_size)

    def edit(self, page: TypeName.tabular_page):
        page.props.set_overwrite_option(True)
        page.props.write_select_at('edit_status', self.status_enum['append'])
        page.props.write_checkbox_at('not_available', False)
        page.execute()
