from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Optional, Union

from .block_contents import BlockContents, TextContents, InlinePageContents
from ...api_format.encode import RichTextContentsEncoder
from ...api_format.parse import BlockChildrenParser
from ...gateway import GetBlockChildren, AppendBlockChildren
from ...struct import Editor, BridgeEditor, GroundEditor, MasterEditor, drop_empty_request
from ...struct.editor import AbstractEditor


class SupportedBlock(MasterEditor, metaclass=ABCMeta):
    @classmethod
    def create_new(cls, caller: Editor):
        return cls(caller, '')


class ChildBearingBlock(SupportedBlock, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, caller: Union[Editor, AbstractEditor], block_id: str):
        super().__init__(caller, block_id)
        self.is_supported_type = True
        self.can_have_children = True
        self.has_children = False

        self.children = BlockChildren(self)
        self.agents.update(children=self.children)

    def goto_last_children(self) -> SupportedBlock:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.children[-1]
        except IndexError:
            print('indentation not possible!')
            cursor = self
        return cursor

    @abstractmethod
    def preview(self):
        return {'contents': "unpack contents here",
                'children': "unpack children here"}

    @abstractmethod
    @drop_empty_request
    def execute(self):
        """
        1. since self.children go first than self.new_children,
            assigning a multi-indented structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.tabular,
            have to refer to self.master_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """
        return


class BlockChildren(Editor):
    def __init__(self, caller: ChildBearingBlock):
        super().__init__(caller)
        self.caller = caller
        self._normal = NormalBlockChildrenContainer(self)
        self._new = NewBlockChildrenContainer(self)

    @property
    def values(self):
        return self._normal.values + self._new.values

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any([self._normal, self._new])

    @property
    def parent(self) -> ChildBearingBlock:
        parent = self.master.caller.master
        if isinstance(parent, ChildBearingBlock):
            return parent
        raise ValueError

    def fetch(self, page_size=0):
        gateway = GetBlockChildren(self)
        response = gateway.execute(page_size=page_size)
        parser = BlockChildrenParser(response)
        self._normal.apply_parser(parser)

    def fetch_descendants(self, page_size=0):
        self.fetch(page_size)
        for child in self._normal:
            if child.has_children and isinstance(child, ChildBearingBlock):
                child.children.fetch_descendants(page_size)

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

    def create_text_block(self) -> TextBlock:
        return self._new.create_text_block()

    def create_inline_page(self) -> InlinePageBlock:
        return self._new.create_inline_page()

    def indent_next_block(self) -> BlockChildren:
        """if not possible, the cursor will stay at its position."""
        for child in reversed(self.values):
            if hasattr(child, 'children') and isinstance(child, ChildBearingBlock):
                return child.children
        else:
            print('indentation not possible!')
            return self

    def exdent_next_block(self) -> BlockChildren:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.parent.children
        except AttributeError:
            print('exdentation not possible!')
            cursor = self
        return cursor

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self._new.push_carrier(carrier)


class BlockChildrenContainer(Editor, metaclass=ABCMeta):
    pass


class NormalBlockChildrenContainer(BridgeEditor, BlockChildrenContainer):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self.values: list[SupportedBlock] = []

    def __iter__(self):
        return iter(self.values)

    def apply_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            if child_parser.is_supported_type:
                if child_parser.is_page_block:
                    child = InlinePageBlock(self, child_parser.block_id)
                else:
                    child = TextBlock(self, child_parser.block_id)
                child.contents.apply_block_parser(child_parser)
            else:
                child = UnsupportedBlock(child_parser.block_id)
            self.values.append(child)

    def reads(self):
        return [child.fully_read for child in self]

    def reads_rich(self):
        return [child.fully_read_rich() for child in self]


class NewBlockChildrenContainer(GroundEditor, BlockChildrenContainer):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self._chunks: list[list[ContentsBlock]] = []
        self._requests: list[Union[AppendBlockChildren, InlinePageBlock]] = []
        self.gateway = AppendBlockChildren(self)
        self._chunk_interrupted = True

    def __iter__(self):
        return iter(self.values)

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any(child for child in self)

    @property
    def values(self) -> list[ContentsBlock]:
        res = []
        for chunk in self._chunks:
            if type(chunk) == list:
                res.extend(chunk)
            else:
                res.append(chunk)
        return res

    def preview(self):
        res = []
        for request in self._requests:
            if isinstance(request, AppendBlockChildren):
                res.append(request.unpack())
            elif isinstance(request, InlinePageBlock):
                res.append(request.preview())
        return res

    def execute(self):
        for request, chunk in zip(self._requests, self._chunks):
            if isinstance(request, AppendBlockChildren):
                response = request.execute()
                if not response:
                    continue
                parsers = BlockChildrenParser(response)
                for parser, new_child in zip(parsers, chunk):
                    new_child.contents.apply_block_parser(parser)
            elif isinstance(request, InlinePageBlock):
                request.execute()
            else:
                print('WHAT DID YOU DO?!')
                pass
        for child in self.values:
            child.execute()
        res = self.values.copy()
        self.values.clear()
        self._requests.clear()
        return res

    def create_text_block(self):
        if self._chunk_interrupted:
            self.gateway = AppendBlockChildren(self)
            self._requests.append(self.gateway)
            self._chunks.append([])
            self._chunk_interrupted = False
        child = TextBlock.create_new(self)
        self._chunks[-1].append(child)
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child
    """
    def create_inline_page(self):
        if self._chunk_interrupted:
            self.gateway = AppendBlockChildren(self)
            self._requests.append(self.gateway)
            self._chunks.append([])
            self._chunk_interrupted = False
        child = InlinePageBlock.create_new(self)
        self._chunks[-1].append(child)
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child
    """
    def create_inline_page(self):
        child = InlinePageBlock.create_new(self)
        self._requests.append(child)
        self._chunks.append([child])
        self._chunk_interrupted = True
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child


    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)


class ContentsBlock(ChildBearingBlock, metaclass=ABCMeta):
    def __init__(self, caller: Union[Editor], block_id: str):
        super().__init__(caller, block_id)
        self.contents: Optional[BlockContents] = None

    def fully_read(self):
        return {'contents': self.contents.read(),
                'children': self.children.reads()}

    def fully_read_rich(self):
        return {'contents': self.contents.read_rich(),
                'children': self.children.reads_rich()}

    def preview(self):
        return {'contents': self.contents.preview(),
                **self.children.preview()}


class TextBlock(ContentsBlock):
    def __init__(self, caller: Union[Editor], block_id: str):
        super().__init__(caller=caller, block_id=block_id)
        if isinstance(caller, NewBlockChildrenContainer):
            self.contents = TextContents(self, caller)
        else:
            self.contents = TextContents(self)
        self.agents.update(contents=self.contents)

    @property
    def master_name(self):
        return self.contents.read

    def execute(self):
        if self.yet_not_created:
            pass
        else:
            self.contents.execute()
            self.children.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='text')

    def fully_read_rich(self):
        return dict(**super().fully_read(), type='text')


class InlinePageBlock(ContentsBlock):
    def __init__(self, caller: Union[Editor], page_id: str):
        super().__init__(caller, page_id)
        """if isinstance(caller, NewBlockChildrenContainer):
            self.contents = InlinePageContents(self, caller)
        else:
            self.contents = InlinePageContents(self)"""
        self.contents = InlinePageContents(self)
        self.agents.update(contents=self.contents)
        self.title = ''

    @property
    def master_name(self):
        return self.title

    @drop_empty_request
    def execute(self):
        self.contents.execute()
        self.children.execute()

    def fully_read(self):
        return dict(**super().fully_read(), type='page')

    def fully_read_rich(self):
        return dict(**super().fully_read(), type='page')


class UnsupportedBlock(MasterEditor):
    @property
    def master_name(self):
        return self.master_url

    def __init__(self, block_id: str, caller: Optional[Editor] = None):
        super().__init__(caller, block_id)

    @property
    def parent(self) -> ChildBearingBlock:
        return self.parent

    def fully_read(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def fully_read_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def preview(self):
        return {}

    def execute(self):
        return {}
