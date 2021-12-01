from notion_zap.cli import editors


def remove_dummy_blocks(page: editors.common.ItemsBearer):
    duplicate = False
    removed = 0
    for block in page.items:
        if block.archived:
            continue
        # remove "blank" blocks
        if isinstance(block, editors.TextItem) and \
                block.contents.read().split() == '':
            block.contents.archive()
            removed += 1
        # remove duplicate contents (page_block)
        if isinstance(block, editors.PageItem) and \
                page.block_name in block.contents.read():
            if not duplicate:
                duplicate = True
            else:
                block.contents.archive()
                removed += 1
    if removed and isinstance(page, editors.PageRow):
        page.props.write_text_at('link_to_contents', '')
    return removed
