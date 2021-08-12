from __future__ import annotations
from typing import Optional
from abc import ABCMeta

from notion_py.gateway.structure import Requestor
from notion_py.gateway.parse import BlockChildParser, BlockChildrenParser
from notion_py.gateway.read import RetrieveBlockChildren
from notion_py.gateway.write import AppendBlockChildren, UpdateBlockContents
from notion_py.gateway.write.block_contents import BlockContents
from notion_py.gateway.write.block_child_stash import BlockChildrenStash


class Block(Requestor, metaclass=ABCMeta):
    def __init__(self, block_id: str, parent_id: Optional[str],
                 can_have_children: bool, has_children: bool):
        self.block_id = block_id
        self.parent_id = parent_id
        self.can_have_children = can_have_children
        self._has_children = False
        self.has_children = has_children

    @property
    def has_children(self):
        return self._has_children

    @has_children.setter
    def has_children(self, value: bool):
        self._has_children = (self._has_children or value)

    def fetch_children(self, child_editors: list[Block]):
        pass


class ContentsBlock(Block):
    # TODO : API 지원될 때까지 개발 보류
    def __init__(self, parsed_block: BlockChildParser, parent_id=''):
        super().__init__(parsed_block.block_id,
                         parent_id if parent_id else None,
                         parsed_block.can_have_children,
                         parsed_block.has_children)
        self._update_contents = UpdateBlockContents(self.block_id)
        self.contents: BlockContents = self._update_contents.contents
        self.contents.fetch(parsed_block)

    def apply(self):
        return []

    def execute(self):
        return []


class UnsupportedBlock(Block):
    def __init__(self, parsed_block: BlockChildParser, parent_id=''):
        super().__init__(parsed_block.block_id,
                         parent_id if parent_id else None,
                         False, False)
        self.contents: BlockContents = BlockContents()
        self.contents.fetch(parsed_block)

    def apply(self):
        return []

    def execute(self):
        return []


class ChildbearingBlock(Block):
    # TODO : recursive_apply 가능하도록 고치기.
    #  GenerativeRequestor 클래스를 따로 만들어서 Block의 상위 클래스로 두기.
    #  BasicPage 클래스에도 적용.
    def __init__(self, block_id='', parent_id=''):
        super().__init__(block_id, parent_id, True, False)
        self._append_blocks = AppendBlockChildren(self.block_id)
        self.children: BlockChildren = self._append_blocks.children

    def apply(self):
        res = [self._append_blocks.apply()]
        for child_editor in self.children.read:
            res.append(child_editor.apply())
        return res

    def execute(self):
        res = [self._append_blocks.execute()]
        for child_editor in self.children.read:
            res.append(child_editor.execute())
        return res

    def fetch_children(self, child_editors: list[Block]):
        if child_editors:
            self.children.fetch(child_editors)
            self.has_children = True

    @classmethod
    def from_direct_retrieve(cls, block_id):
        self = cls(block_id)
        self.fetch_children(cls._get_child_editors(block_id))
        return self

    @classmethod
    def from_direct_retrieve_recursively(cls, block_id):
        self = cls(block_id)
        self.fetch_children(cls._get_child_editors_recursively(block_id))
        return self

    @classmethod
    def _get_child_editors(cls, block_id):
        response = RetrieveBlockChildren(block_id)
        parsed_children = BlockChildrenParser.from_response(response)
        child_editors = []
        for parsed_block in parsed_children.values:
            if parsed_block.is_supported_type:
                if parsed_block.can_have_children:
                    child_editors.append(ChildbearingContentsBlock(parsed_block, block_id))
                else:
                    child_editors.append(ContentsBlock(parsed_block, block_id))
            else:
                child_editors.append(UnsupportedBlock(parsed_block, block_id))
        return child_editors

    @classmethod
    def _get_child_editors_recursively(cls, block_id):
        child_editors = cls._get_child_editors(block_id)
        for child in child_editors:
            if child.has_children:
                grandchildren = cls._get_child_editors_recursively(child.block_id)
                child.fetch_children(grandchildren)
        return child_editors


class ChildbearingContentsBlock(ContentsBlock, ChildbearingBlock):
    def __init__(self, parsed_block: BlockChildParser, parent_id=''):
        ChildbearingBlock.__init__(self, block_id=parsed_block.block_id)
        ContentsBlock.__init__(self, parsed_block, parent_id=parent_id)


class BlockChildren(BlockChildrenStash):
    def __init__(self):
        super().__init__()
        self.read: list[Block] = []

    def fetch(self, value: list[Block]):
        if self._overwrite:
            self.read = value
        else:
            self.read.extend(value)
