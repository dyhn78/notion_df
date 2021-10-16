from .common.editor import ReadingDBEditor
from notion_py.interface.utility import stopwatch
from ...interface.editor.abs_supported.abs_child_bearing import ChildBearingBlock
from ...interface.editor.inline import TextBlock, InlinePageBlock


class ReadingDBDuplicateRemover(ReadingDBEditor):
    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist.elements:
            page.sphere.fetch_children()
            removed = remove_dummy_blocks(page)
            if removed:
                page.props.write_text_at('link_to_contents', '')
                stopwatch(f'중복 {removed} 개 제거: {page.title}')
                page.execute()

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.make_filter.select_at('media_type')
        ft_media = maker.equals_to_any(maker.prop_value_groups['book'])
        # maker = query.make_filter.text_at('title')
        # ft_media &= maker.starts_with('칸트의')
        query.push_filter(ft_media)
        query.execute(request_size)


def remove_dummy_blocks(page: ChildBearingBlock):
    duplicate = False
    removed = 0
    for block in page.sphere.children:
        if block.archived:
            continue
        # remove "blank" blocks
        if isinstance(block, TextBlock) and \
                block.contents.read().split() == '':
            block.contents.archive()
            removed += 1
        # remove duplicate contents (page_block)
        if isinstance(block, InlinePageBlock) and \
                page.master_name in block.contents.read():
            if not duplicate:
                duplicate = True
            else:
                block.contents.archive()
                removed += 1
    return removed
