from __future__ import annotations

from abc import ABCMeta
from typing import Union, Iterator

from notion_zap.cli.gateway import requestors, parsers
from ..with_children import ChildrenBearer, BlockChildren
from ...editor_exceptions import BlockTypeError, NoParentFoundError
from ...base import BlockEditor, MasterEditor, Editor


class ItemsBearer(ChildrenBearer, metaclass=ABCMeta):
    def __init__(self, caller: Union[BlockEditor, Editor]):
        super().__init__(caller)
        self.caller = caller
        self.attachments = ItemAttachments(self)

    @property
    def children(self) -> ItemAttachments:
        return self.attachments

    def _fetch_children(self, request_size=0):
        self.children.fetch(request_size)


class ItemAttachments(BlockChildren):
    def __init__(self, caller: ItemsBearer):
        super().__init__(caller)
        self.caller = caller

        from .updater import ItemsUpdater
        self.update = ItemsUpdater(self)

        from .creator import ItemsCreator
        self.create = ItemsCreator(self)

    def attach(self, child: MasterEditor):
        if not self.master.can_have_children:
            raise BlockTypeError(self.master)

        # TODO: child의 이전 parent 로부터 먼저 detach 해야 한다.

        from ...inline import TextItem, PageItem
        if child.yet_not_created:
            if isinstance(child, TextItem):
                self.create.attach_text_item(child)
            elif isinstance(child, PageItem):
                self.create.attach_page_item(child)
            else:
                raise ValueError(f"{child=}")
        else:
            self.update.attach_item(child)

    def detach(self, child: MasterEditor):
        raise NotImplementedError

    def create_text(self):
        from ...inline import TextItem
        return TextItem(self, '')

    def create_page(self):
        from ...inline import PageItem
        return PageItem(self, '')

    def fetch(self, request_size=0):
        requestor = requestors.GetBlockChildren(self)
        response = requestor.execute(request_size)
        parser = parsers.BlockChildrenParser(response)
        self.update.apply_children_parser(parser)

    def indent_cursor(self) -> ItemAttachments:
        """this returns new 'cursor' where you can use of create_xx method.
        raises BlockTypeError if no child can_have_children."""
        for child in reversed(self.list_all()):
            if isinstance(child, ItemsBearer) and child.can_have_children:
                return child.attachments
        else:
            raise BlockTypeError(self.master)

    def try_indent_cursor(self):
        """this returns new 'cursor' where you can use of create_xx method.
        returns <self> if no child can_have_children."""
        try:
            return self.indent_cursor()
        except BlockTypeError:
            return self

    def exdent_cursor(self) -> ItemAttachments:
        """this returns new 'cursor' where you can use of create_xx method.
        raises NoParentFoundError if failed."""
        parent = self.parent
        try:
            assert isinstance(parent, ItemsBearer)
            return parent.attachments
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

    def list_all(self) -> list[MasterEditor]:
        return self.update.blocks + self.create.blocks

    def iter_all(self) -> Iterator[MasterEditor]:
        return iter(self.list_all())

    def reads(self):
        return self.update.reads()

    def reads_rich(self):
        return self.update.reads_rich()
