from typing import Union

from notion_zap.cli.gateway import parsers
from .leaders import ItemChildren
from ...structs.leaders import Block
from ...structs.followers import ListEditor


class ItemsUpdater(ListEditor):
    def __init__(self, caller: ItemChildren):
        super().__init__(caller)
        self.caller = caller
        self._values = []

    def apply_children_parser(self, children_parser: parsers.BlockChildrenParser):
        from ..item import Item
        from ...items.parser_logic import get_type_of_block_parser
        for parser in children_parser:
            block_type = get_type_of_block_parser(parser)
            child = block_type(self, parser.block_id)
            if isinstance(child, Item):
                child.contents.apply_block_parser(parser)
            self.attach_item(child)

    def attach_item(self, child):
        self.values.append(child)

    @property
    def values(self) -> list[Union[Block]]:
        return self._values

    def __iter__(self):
        return iter(self.values)
