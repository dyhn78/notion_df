from notion_py.interface.editor.common.with_items import ItemsBearer
from notion_py.interface.utility import stopwatch
from .common.struct import ReadingDBController
from ...interface.editor.inline import TextItem, PageItem


class ReadingDBDuplicateRemover(ReadingDBController):
    def execute(self, request_size=0):
        self.make_query(request_size)
        for page in self.pagelist:
            page.attachments.fetch()
            removed = remove_dummy_blocks(page)
            if removed:
                page.props.write_text_at('link_to_contents', '')
                stopwatch(f'중복 {removed} 개 제거: {page.title}')
                page.save()

    def make_query(self, request_size):
        query = self.pagelist.open_query()
        maker = query.filter_maker.select_at('media_type')
        ft_media = maker.equals_to_any(maker.prop_value_groups['book'])
        # maker = query.filter_maker.text_at('title')
        # ft_media &= maker.starts_with('칸트의')
        query.push_filter(ft_media)
        query.execute(request_size)


def remove_dummy_blocks(page: ItemsBearer):
    duplicate = False
    removed = 0
    for block in page.attachments:
        if block.archived:
            continue
        # remove "blank" blocks
        if isinstance(block, TextItem) and \
                block.contents.reads().split() == '':
            block.contents.archive()
            removed += 1
        # remove duplicate contents (page_block)
        if isinstance(block, PageItem) and \
                page.block_name in block.contents.reads():
            if not duplicate:
                duplicate = True
            else:
                block.contents.archive()
                removed += 1
    return removed
