from notion_zap.cli import blocks
from notion_zap.cli.blocks.shared.page import PageBlock


def remove_dummy_blocks(page: PageBlock):
    duplicate = False
    removed = 0
    for block in page.items:
        if block.is_archived:
            continue
        # remove "blank" blocks
        if isinstance(block, blocks.TextItem) and \
                block.read_contents().split() == '':
            block.archive()
            removed += 1
        # remove duplicate contents (page_block)
        if isinstance(block, blocks.PageItem) and \
                page.block_name in block.read_contents():
            if not duplicate:
                duplicate = True
            else:
                block.archive()
                removed += 1
    if removed and isinstance(page, blocks.PageRow):
        page.write_text(key_alias='link_to_contents', value='')
    return removed
