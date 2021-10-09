from .regular_scrap import ReadingDBEditor
from notion_py.interface import TypeName


class ReadingDBStatusResolver(ReadingDBEditor):
    def execute(self):
        self.make_query()
        self.pagelist.run_query()
        for page in self.pagelist.elements:
            self.edit(page)

    def make_query(self):
        query = self.pagelist.query
        maker = query.make_filter.select_at('media_type')
        ft = maker.equals_to_any(maker.prop_value_groups['book'])
        maker = query.make_filter.select_at('edit_status')
        ft &= maker.equals_to_any(maker.prop_value_groups['need_resets'])
        """
        maker = query.make_filter.checkbox_at('not_available')
        ft |= maker.equals(True)
        """
        query.push_filter(ft)

    def edit(self, page: TypeName.tabular_page):
        page.props.set_overwrite_option(True)
        page.props.write_select_at('edit_status', self.status_enum['append'])
        page.props.write_checkbox_at('not_available', False)
        page.execute()
