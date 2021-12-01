from __future__ import annotations

from abc import ABCMeta

from notion_zap.cli.gateway import requestors, parsers
from ..with_children import ChildrenBearer, BlockChildren
from ...structs.leaders import Block, GeneralAttachments
from ...structs.exceptions import BlockTypeError, NoParentFoundError


class ItemsBearer(ChildrenBearer, metaclass=ABCMeta):
    def __init__(self, caller: GeneralAttachments, id_or_url: str):
        super().__init__(caller, id_or_url)
        self.items = ItemChildren(self)

    @property
    def children(self) -> ItemChildren:
        return self.items

    def _fetch_children(self, request_size=0):
        self.children.fetch(request_size)


class ItemChildren(BlockChildren):
    def __init__(self, caller: ItemsBearer):
        super().__init__(caller)
        self.caller = caller

        from .updater import ItemsUpdater
        self.update = ItemsUpdater(self)

        from .creator import ItemsCreator
        self.create = ItemsCreator(self)

    def attach(self, child: Block):
        super().attach(child)

        if not self.master.can_have_children:
            raise BlockTypeError(self.master)

        from ...items import TextItem, PageItem
        if child.block_id:
            self.update.attach_item(child)
        else:
            if isinstance(child, TextItem):
                self.create.attach_text_item(child)
            elif isinstance(child, PageItem):
                self.create.attach_page_item(child)
            else:
                raise ValueError(f"{child=}")

    def detach(self, child: Block):
        raise NotImplementedError

    def create_text(self):
        from ...items import TextItem
        return TextItem(self, '')

    def create_page(self):
        from ...items import PageItem
        return PageItem(self, '')

    def fetch(self, request_size=0):
        requestor = requestors.GetBlockChildren(self)
        response = requestor.execute(request_size)
        parser = parsers.BlockChildrenParser(response)
        self.update.apply_children_parser(parser)

    def indent_cursor(self) -> ItemChildren:
        """this returns new 'cursor' where you can use of create_xx method.
        raises BlockTypeError if no child can_have_children."""
        for child in reversed(self.list_all()):
            if isinstance(child, ItemsBearer) and child.can_have_children:
                return child.items
        else:
            raise BlockTypeError(self.master)

    def try_indent_cursor(self):
        """this returns new 'cursor' where you can use of create_xx method.
        returns <self> if no child can_have_children."""
        try:
            return self.indent_cursor()
        except BlockTypeError:
            return self

    def exdent_cursor(self) -> ItemChildren:
        """this returns new 'cursor' where you can use of create_xx method.
        raises NoParentFoundError if failed."""
        parent = self.parent
        try:
            assert isinstance(parent, ItemsBearer)
            return parent.items
        except AssertionError:
            raise NoParentFoundError(self.master)

    def try_exdent_cursor(self):
        """this returns new 'cursor' where you can use of create_xx method.
        returns <self> if failed."""
        try:
            return self.exdent_cursor()
        except NoParentFoundError:
            return self

    def save(self):
        self.update.save()
        new_children = self.create.save()
        self.update.blocks.extend(new_children)
        self.create.clear()

    def save_info(self):
        return {'children': self.update.save_info(),
                'new_children': self.create.save_info()}

    def save_required(self):
        return (self.update.save_required()
                or self.create.save_required())

    def __getitem__(self, idx: int):
        return self.list_all()[idx]

    def list_all(self) -> list[Block]:
        return self.update.blocks + self.create.blocks

    def reads(self):
        return self.update.reads()

    def reads_rich(self):
        return self.update.reads_rich()
