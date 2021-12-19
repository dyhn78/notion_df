from notion_zap.cli import editors
from notion_zap.cli.editors.shared.page import PageBlock


def remove_dummy_blocks(page: PageBlock):
    duplicate = False
    removed = 0
    for block in page.items:
        if block.archived:
            continue
        # remove "blank" blocks
        if isinstance(block, editors.TextItem) and \
                block.read_contents().split() == '':
            block.archive()
            removed += 1
        # remove duplicate contents (page_block)
        if isinstance(block, editors.PageItem) and \
                page.block_name in block.read_contents():
            if not duplicate:
                duplicate = True
            else:
                block.archive()
                removed += 1
    if removed and isinstance(page, editors.PageRow):
        page.write_text(tag='link_to_contents', value='')
    return removed
