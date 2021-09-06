from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Optional, Union

from .contents import BlockContents, TextContents, InlinePageContents
from .unsupported import UnsupportedBlock
from ...api_format.encode import RichTextContentsEncoder
from ...api_format.parse import BlockChildrenParser
from ...gateway import GetBlockChildren, AppendBlockChildren
from ...struct import MasterEditor, Editor, BridgeEditor, GroundEditor
from ...utility import page_id_to_url


class DefaultBlock(MasterEditor, metaclass=ABCMeta):
    def __init__(self, master_id: str, caller: Optional[Editor] = None):
        super().__init__(master_id, caller)
        self.is_supported_type = False
        self.can_have_children = False
        self.has_children = False

    @property
    def master_url(self):
        return page_id_to_url(self.master_id)

    @property
    def parent_id(self):
        try:
            return self.caller.master_id
        except AttributeError:
            if self.master_url:
                message = f'cannot find parent_id at: {self.master_url}'
            else:
                message = (f"ERROR: provide master_id or parent_id for this block;\n"
                           f"editor info:\n"
                           f"{self.preview()}")
            raise AttributeError(message)

    def goto_parent(self) -> Union[ChildBearingBlock, DefaultBlock]:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.caller.master
        except AttributeError:
            print('exdentation not possible!')
            cursor = self
        return cursor


class SupportedBlock(DefaultBlock, metaclass=ABCMeta):
    @classmethod
    def create_new(cls, caller: Editor):
        return cls(master_id='', caller=caller)

    @property
    def yet_not_created(self):
        if self.master_id:
            return False
        else:
            assert self.parent_id
            return True

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def read_rich(self):
        pass


class ChildBearingBlock(SupportedBlock, metaclass=ABCMeta):
    @abstractmethod
    def __init__(self, block_id: str,
                 caller: Optional[Editor] = None):
        super().__init__(block_id, caller)
        self.is_supported_type = True
        self.can_have_children = True
        self.has_children = False

        self.children = BlockChildren(self)
        self.agents.update(children=self.children)

    def goto_parent(self) -> ChildBearingBlock:
        return super().goto_parent()

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
        self.caller = caller
        self._normal = NormalBlockChildrenContainer(self)
        self._new = NewBlockChildrenContainer(self)

    def __iter__(self) -> list[SupportedBlock]:
        return self._normal.values + self._new.values

    def __getitem__(self, index: int):
        return self.__iter__()[index]

    def __len__(self):
        return len(self.__iter__())

    def __bool__(self):
        return any([self._normal, self._new])

    def sync_master_id(self):
        self._new.sync_master_id()

    def fetch(self, page_size=0):
        gateway = GetBlockChildren(self.master_id)
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
        for child in reversed(self.__iter__()):
            if hasattr(child, 'children') and isinstance(child, ChildBearingBlock):
                return child.children
        else:
            print('indentation not possible!')
            return self

    def exdent_next_block(self) -> BlockChildren:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.caller.goto_parent().children
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
        return self.values

    def apply_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            if child_parser.is_supported_type:
                if child_parser.is_page_block:
                    child = InlinePageBlock(child_parser.block_id)
                else:
                    child = TextBlock(child_parser.block_id)
                child.contents.apply_block_parser(child_parser)
            else:
                child = UnsupportedBlock(child_parser.block_id)
            self.values.append(child)

    def reads(self):
        return [child.read for child in self]

    def reads_rich(self):
        return [child.read_rich for child in self]


class NewBlockChildrenContainer(GroundEditor, BlockChildrenContainer):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self._chunks: list[list[ContentsBlock]] = []
        self._requests: list[Union[AppendBlockChildren, InlinePageBlock]] = []
        self.gateway: Optional[AppendBlockChildren] = None
        self._chunk_interrupted = True

    def __iter__(self) -> list[ContentsBlock]:
        return self.values

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
            res.extend(*chunk)
        return res

    def sync_master_id(self):
        self.gateway.target_id = self.master_id

    def preview(self):
        return [request.preview() for request in self._requests]

    def execute(self):
        for request, chunk in zip(self._requests, self._chunks):
            if isinstance(request, AppendBlockChildren):
                response = request.execute()
                parsers = BlockChildrenParser(response)
                for parser, new_child in zip(parsers, chunk):
                    new_child.contents.apply_block_parser(parser)
            elif isinstance(request, InlinePageBlock):
                request.execute()
            else:
                print('WHAT DID YOU DO?!')
                pass
        res = self.values.copy()
        self.values.clear()
        self._requests.clear()
        return res

    def create_text_block(self):
        if self._chunk_interrupted:
            self.gateway = AppendBlockChildren(self.caller.master_id)
            self._requests.append(self.gateway)
            self._chunks.append([])
            self._chunk_interrupted = False
        child = TextBlock.create_new_as_appended(self, self.gateway)
        self._chunks[-1].append(child)
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child

    def create_inline_page(self):
        child = InlinePageBlock.create_new(self)
        self._requests.append(child)
        self._chunks.append([])
        self._chunks[-1].append(child)
        self._chunk_interrupted = True
        assert (id(child) == id(self[-1]) == id(self._chunks[-1][-1]))
        return child

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)


class ContentsBlock(ChildBearingBlock, metaclass=ABCMeta):
    def __init__(self, block_id: str, caller: Optional[Editor] = None):
        super().__init__(block_id, caller)
        self.contents: Optional[BlockContents] = None

    def sync_master_id(self):
        self.children.sync_master_id()

    def read(self):
        return {'contents': self.contents.read(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'contents': self.contents.read_rich(),
                'children': self.children.reads_rich()}

    def preview(self):
        return {'contents': self.contents.preview(),
                **self.children.preview()}


class TextBlock(ContentsBlock):
    def __init__(self, block_id: str, caller: Optional[Editor] = None,
                 gateway_alternative: Optional[AppendBlockChildren] = None):
        super().__init__(block_id, caller=caller)
        self.contents = TextContents(self, gateway_alternative)
        self.agents.update(contents=self.contents)

    @classmethod
    def create_new_as_appended(cls, caller: Editor, gateway: AppendBlockChildren):
        return cls(block_id='', caller=caller, gateway_alternative=gateway)

    def execute(self):
        if self.caller:
            return self.caller.master.execute()
        else:
            self.contents.execute()
            self.children.execute()

    def read(self):
        return dict(**super().read(), type='text')

    def read_rich(self):
        return dict(**super().read(), type='text')


class InlinePageBlock(ContentsBlock):
    def __init__(self, page_id: str, caller: Optional[Editor] = None):
        super().__init__(page_id, caller)
        parent_id = self.parent_id if self.yet_not_created else ''
        self.contents = InlinePageContents(self, parent_id)
        self.agents.update(contents=self.contents)
        self.title = ''

    def execute(self):
        if self.caller:
            return self.caller.master.execute()
        else:
            self.contents.execute()
            self.children.execute()

    def read(self):
        return dict(**super().read(), type='page')

    def read_rich(self):
        return dict(**super().read(), type='page')
