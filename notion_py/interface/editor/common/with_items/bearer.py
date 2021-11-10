from __future__ import annotations

from abc import ABCMeta
from typing import Union, Iterator

from notion_py.interface.gateway import requestors, parsers
from ..with_children import ChildrenBearer, BlockChildren
from ...editor_exceptions import BlockTypeError, NoParentFoundError
from ...struct import BlockEditor, MasterEditor, Editor


class ItemsBearer(ChildrenBearer, metaclass=ABCMeta):
    def __init__(self, caller: Union[BlockEditor, Editor]):
        super().__init__(caller)
        self.caller = caller
        self.attachments = ItemAttachments(self)

    @property
    def children(self) -> BlockChildren:
        return self.attachments


class ItemAttachments(BlockChildren):
    def __init__(self, caller: ItemsBearer):
        super().__init__(caller)
        self.caller = caller

        from .updater import ItemsUpdater
        self.update = ItemsUpdater(self)

        from .creator import ItemsCreator
        self.create = ItemsCreator(self)

    def create_text(self):
        from ...inline import TextItem
        return TextItem(self, '')

    def create_page(self):
        from ...inline import PageItem
        return PageItem(self, '')

    def attach_text(self, child):
        from ...inline import TextItem
        assert isinstance(child, TextItem)
        if not self.master.can_have_children:
            raise BlockTypeError(self.master)
        if child.yet_not_created:
            self.create.attach_text_item(child)
        else:
            self.update.attach_item(child)

    def attach_page(self, child):
        from ...inline import PageItem
        assert isinstance(child, PageItem)
        if not self.master.can_have_children:
            raise BlockTypeError(self.master)
        if child.yet_not_created:
            self.create.attach_page_item(child)
        else:
            self.update.attach_item(child)

    # def create_page_alt(self):
    #     if not self.master.can_have_children:
    #         raise BlockTypeError(self.master)
    #     from ...inline.page_item import PageItem
    #     space = self.create.make_space_for_page_item()
    #     item = PageItem(space, '')

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
