from __future__ import annotations

from abc import ABCMeta
from collections import defaultdict
from typing import Union, Iterator

from notion_py.interface.editor.common.with_children import ChildrenBearer, BlockChildren
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import GetBlockChildren
from ..struct import PointEditor, MasterEditor, Editor
from ..supported import SupportedBlock


class ItemsBearer(ChildrenBearer, metaclass=ABCMeta):
    def __init__(self, caller: Union[PointEditor, Editor], block_id: str):
        super().__init__(caller, block_id)
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
        self._normal = ItemsUpdater(self)

        from .creator import ItemsCreator
        self._new = ItemsCreator(self)

        self._by_id = {}
        self._by_title = defaultdict(list)

    @property
    def by_id(self) -> dict[str, MasterEditor]:
        return self._by_id

    @property
    def by_title(self) -> dict[str, list[MasterEditor]]:
        return self._by_title

    def list_all(self) -> list[SupportedBlock]:
        return self._normal.blocks + self._new.blocks

    def iter_all(self) -> Iterator[MasterEditor]:
        return iter(self.list_all())

    def fetch(self, request_size=0):
        gateway = GetBlockChildren(self)
        response = gateway.execute(request_size)
        parser = BlockChildrenParser(response)
        self._normal.apply_parser(parser)

    def save_required(self):
        return (self._normal.save_required()
                or self._new.save_required())

    def save_info(self):
        return {'children': self._normal.save_info(),
                'new_children': self._new.save_info()}

    def save(self):
        self._normal.save()
        new_children = self._new.save()
        self._normal.blocks.extend(new_children)
        self._new.clear()

    def reads(self):
        return self._normal.reads()

    def reads_rich(self):
        return self._normal.reads_rich()

    def create_text_block(self):
        return self._new.create_text_item()

    def create_page_block(self):
        return self._new.create_page_item()

    def indent_next_block(self) -> ItemAttachments:
        """if not possible, the cursor will stay at its position."""
        for child in reversed(self.list_all()):
            if isinstance(child, ItemsBearer):
                return child.attachments
        else:
            print('indentation not possible!')
            return self

    def exdent_next_block(self) -> ItemAttachments:
        """if not possible, the cursor will stay at its position."""
        parent = self.parent
        if isinstance(parent, ItemsBearer):
            cursor = parent.attachments
        else:
            print('exdentation not possible!')
            cursor = self
        return cursor
