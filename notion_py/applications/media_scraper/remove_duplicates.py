from .common.editor import ReadingDBEditor
from notion_py.interface import TypeName, stopwatch


class ReadingDBDuplicateRemover(ReadingDBEditor):
    def execute(self, page_size=0):
        self.make_query(page_size)
        for page in self.pagelist.elements:
            page.sphere.fetch_children()
            remove_dummy_blocks(page)

    def make_query(self, page_size):
        query = self.pagelist.query
        maker = query.make_filter.select_at('media_type')
        ft_media = maker.equals_to_any(maker.prop_value_groups['book'])
        # maker = query.make_filter.text_at('title')
        # ft_media &= maker.starts_with('칸트의')
        query.push_filter(ft_media)
        self.pagelist.run_query(page_size=page_size)


def remove_dummy_blocks(page: TypeName.tabular_page):
    duplicate = False
    removed = 0
    for block in page.sphere.children:
        if block.archived:
            continue
        # remove "blank" blocks
        if isinstance(block, TypeName.text_block) and \
                block.contents.read().split() == '':
            block.contents.archive()
            removed += 1
        # remove duplicate contents (page_block)
        if isinstance(block, TypeName.inline_page) and \
                page.title in block.contents.read():
            if not duplicate:
                duplicate = True
            else:
                block.contents.archive()
                removed += 1
    if removed:
        page.props.write_text_at('link_to_contents', '')
        stopwatch(f'중복 {removed} 개 제거: {page.title}')
        page.execute()
