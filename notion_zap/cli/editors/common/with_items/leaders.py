from __future__ import annotations

from abc import ABCMeta
from typing import Any

from notion_zap.cli.gateway import requestors, parsers
from ..with_children import ChildrenBearer, BlockChildren
from ...structs.leaders import Block, Registry
from ...structs.exceptions import BlockTypeError


class ItemsBearer(ChildrenBearer, metaclass=ABCMeta):
    def __init__(self, caller: Registry, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.items = ItemChildren(self)

    @property
    def children(self) -> ItemChildren:
        return self.items

    def _fetch_children(self, request_size=0):
        self.children.fetch(request_size)

    def indent_cursor(self) -> ItemsBearer:
        """this returns new 'cursor' where you can use of open_new_xx method.
        raises BlockTypeError if no child can_have_children."""
        for child in reversed(self.items.list_all()):
            if isinstance(child, ItemsBearer) and child.can_have_children:
                return child
        else:
            raise BlockTypeError(self)


class ItemChildren(BlockChildren):
    def __init__(self, caller: ItemsBearer):
        super().__init__(caller)
        self.caller = caller

        from .updater import ItemsUpdater
        self._updater = ItemsUpdater(self)

        from .creator import ItemsCreator
        self._creator = ItemsCreator(self)

    def __getitem__(self, idx: int):
        return self.list_all()[idx]

    def list_all(self) -> list[Block]:
        return self._updater.values + self._creator.values

    def read(self) -> dict[str, Any]:
        return dict(**self._updater.read(),
                    **self._creator.read())

    def richly_read(self) -> dict[str, Any]:
        return dict(**self._updater.richly_read(),
                    **self._creator.richly_read())

    def save(self):
        self._updater.save()
        new_children = self._creator.save()
        self._updater.values.extend(new_children)
        self._creator.clear()

    def save_info(self):
        return {'children': self._updater.save_info(),
                'new_children': self._creator.save_info()}

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
            raise BlockTypeError(self.block)

        from ...items import TextItem, PageItem
        if child.block_id:
            self._updater.attach_item(child)
        else:
            if isinstance(child, TextItem):
                self._creator.attach_text_item(child)
            elif isinstance(child, PageItem):
                self._creator.attach_page_item(child)
            else:
                raise ValueError(f"{child=}")

    def detach(self, child: Block):
        raise NotImplementedError
