from notion_zap.cli.gateway import parsers
from .main import ItemChildren
from ...structs.block_main import Block
from ...structs.save_agents import ListEditor


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
            child = block_type(self.caller, parser.block_id)
            if isinstance(child, Item):
                child.apply_block_parser(parser)
            # do not self.attach_item(child); child will attach to parent themselves

    def attach_item(self, child):
        self.values.append(child)

    @property
    def values(self) -> list[Block]:
        return self._values

    def __iter__(self):
        return iter(self.values)
