from notion_zap.cli.gateway import parsers
from .page_item import PageItem
from .text_item import TextItem
from .unsupported import UnsupportedBlock


def get_type_of_block_parser(parser: parsers.BlockContentsParser):
    if not parser.is_supported_type:
        return UnsupportedBlock
    elif parser.is_page_block:
        return PageItem
    else:
        return TextItem
