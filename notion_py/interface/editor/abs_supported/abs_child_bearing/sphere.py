from __future__ import annotations

from notion_py.interface.common.struct import drop_empty_request
from notion_py.interface.editor.abs_supported.abs_child_bearing import ChildBearingBlock
from notion_py.interface.editor.abs_supported.master import SupportedBlock
from notion_py.interface.editor.struct import PointEditor
from notion_py.interface.encoder import RichTextContentsEncoder
from notion_py.interface.parser import BlockChildrenParser
from notion_py.interface.requestor import GetBlockChildren


class BlockSphere(PointEditor):
    def __init__(self, caller: ChildBearingBlock):
        from .updater import BlockSphereUpdater
        from .creator import BlockSphereCreator
        super().__init__(caller)
        self.caller = caller
        self._normal = BlockSphereUpdater(self)
        self._new = BlockSphereCreator(self)

    def __iter__(self):
        return iter(self.children)

    def __getitem__(self, index: int):
        return self.children[index]

    def __len__(self):
        return len(self.children)

    def __bool__(self):
        return any([self._normal, self._new])

    @property
    def children(self) -> list[SupportedBlock]:
        return self._normal.values + self._new.values

    @property
    def descendants(self) -> list[SupportedBlock]:
        res = []
        res.extend(self.children)
        for child in self.children:
            if isinstance(child, ChildBearingBlock):
                res.extend(child.sphere.descendants)
        return res

    def fetch_children(self, page_size=0):
        gateway = GetBlockChildren(self)
        response = gateway.execute(request_size=page_size)
        parser = BlockChildrenParser(response)
        self._normal.apply_parser(parser)

    def fetch_descendants(self, depth=-1, page_size=0):
        if depth == 0:
            return
        self.fetch_children(page_size)
        for child in self._normal:
            if child.has_children and isinstance(child, ChildBearingBlock):
                child.sphere.fetch_descendants(depth=depth - 1, page_size=page_size)

    def create_text_block(self):
        return self._new.create_text_block()

    def create_page_block(self):
        return self._new.create_page_block()

    def preview(self):
        return {'children': self._normal.preview(),
                'new_children': self._new.preview()}

    @drop_empty_request
    def execute(self):
        self._normal.execute()
        new_children = self._new.execute()
        self._normal.values.extend(new_children)

    def reads(self):
        return self._normal.reads()

    def reads_rich(self):
        return self._normal.reads_rich()

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self._new.push_carrier(carrier)

    def indent_next_block(self) -> BlockSphere:
        """if not possible, the cursor will stay at its position."""
        for child in reversed(self.children):
            if isinstance(child, ChildBearingBlock):
                return child.sphere
        else:
            print('indentation not possible!')
            return self

    def exdent_next_block(self) -> BlockSphere:
        """if not possible, the cursor will stay at its position."""
        if hasattr(self.parent, 'sphere'):
            cursor = self.parent.sphere
        else:
            print('exdentation not possible!')
            cursor = self
        return cursor
