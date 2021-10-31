from notion_py.interface.parser import BlockContentsParser
from . import PageItem, TextItem
from .unsupported import UnsupportedBlock


def get_type_of_block_parser(parser: BlockContentsParser):
    if not parser.is_supported_type:
        return UnsupportedBlock
    elif parser.is_page_block:
        return PageItem
    else:
        return TextItem
