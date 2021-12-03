from __future__ import annotations
from abc import ABCMeta

from notion_zap.cli.gateway import requestors, parsers
from ..with_children import BlockWithChildren, Children
from ...structs.base_logic import Gatherer
from ...structs.block_main import Block
from ...structs.exceptions import InvalidBlockTypeError


class BlockWithItems(BlockWithChildren, metaclass=ABCMeta):
    def __init__(self, caller: Gatherer, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.items = ItemChildren(self)

    @property
    def children(self) -> ItemChildren:
        return self.items

    def _fetch_children(self, request_size=0):
        self.children.fetch(request_size)

    def indent_cursor(self) -> BlockWithItems:
        """this returns new 'cursor' where you can use of open_new_xx method.
        raises InvalidBlockTypeError if no child can_have_children."""
        for child in reversed(self.items.list_all()):
            if isinstance(child, BlockWithItems) and child.can_have_children:
                return child
        else:
            raise InvalidBlockTypeError(self)


class ItemChildren(Children):
    def __init__(self, caller: BlockWithItems):
        super().__init__(caller)
        self.caller = caller
        self.__save_in_process = False

        from .updater import ItemsUpdater
        self._updater = ItemsUpdater(self)

        from .creator import ItemsCreator
        self._creator = ItemsCreator(self)

    def __getitem__(self, idx: int):
        return self.list_all()[idx]

    def list_all(self) -> list[Block]:
        return self._updater.values + self._creator.values

    def save(self):
        if self.__save_in_process:
            return {}
        self.__save_in_process = True
        self._updater.save()
        new_children = self._creator.save()
        self._updater.values.extend(new_children)
        self._creator.clear()
        self.__save_in_process = False

    def save_required(self):
        return (self._updater.save_required()
                or self._creator.save_required())

    def fetch(self, request_size=0):
        requestor = requestors.GetBlockChildren(self)
        response = requestor.execute(request_size)
        parser = parsers.BlockChildrenParser(response)
        self._updater.apply_children_parser(parser)

    def open_text(self, id_or_url: str):
        from ...items import TextItem
        return TextItem(self, id_or_url)

    def open_page(self, id_or_url: str):
        from ...items import PageItem
        return PageItem(self, id_or_url)

    def open_new_text(self):
        return self.open_text('')

    def open_new_page(self):
        return self.open_page('')

    def attach(self, child: Block):
        if not self.block.can_have_children:
            raise InvalidBlockTypeError(self.block)

        from ...items import TextItem, PageItem
        if child.block_id:
            self._updater.attach_item(child)
        else:
            if isinstance(child, TextItem):
                self._creator.attach_text_item(child)
            elif isinstance(child, PageItem):
                self._creator.attach_page_item(child)
            else:
                raise InvalidBlockTypeError(child)

    def detach(self, child: Block):
        """currently unavailable until the official API supports moving blocks."""
        raise NotImplementedError
