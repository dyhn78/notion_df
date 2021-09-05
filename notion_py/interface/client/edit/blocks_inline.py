from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Optional, Union

from notion_py.interface.struct.editor import GroundEditor, BridgeEditor, \
    Editor, MasterEditor
from .eval_empty import eval_empty
from ...api_format.encode import \
    TextContentsWriter, RichTextPropertyEncoder
from ...api_format.encode.block_contents_encode import RichTextContentsEncoder
from ...api_format.parse import \
    BlockChildrenParser, BlockContentsParser, PageParser
from ...gateway import \
    RetrievePage, RetrieveBlock, GetBlockChildren, \
    UpdatePage, CreatePage, UpdateBlock, AppendBlockChildren
from ...utility import page_id_to_url


class AbstractBlock(MasterEditor, metaclass=ABCMeta):
    @property
    def master_url(self):
        return page_id_to_url(self.master_id)


class DefaultBlock(AbstractBlock):
    def __init__(self, block_id: str, caller: Optional[NewBlockChildrenContainer] = None):
        super().__init__(block_id, caller)
        self.is_supported_type = False
        self.can_have_children = False
        self.has_children = False

    def sync_master_id(self):
        pass

    def read(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def read_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported',
                'id': self.master_url}

    def unpack(self):
        return {}

    def execute(self):
        return {}


class SupportedBlock(AbstractBlock):
    @abstractmethod
    def __init__(self, block_id: str,
                 caller: Optional[Union[BridgeEditor, BlockChildrenContainer]] = None):
        super().__init__(block_id, caller)
        self.caller = caller
        self.is_supported_type = True
        self.can_have_children = True
        self.has_children = False

        self.children = BlockChildren(self)
        self.agents.update(children=self.children)

    @classmethod
    def create_new(cls, caller: Union[BridgeEditor, BlockChildrenContainer]):
        return cls(block_id='', caller=caller)

    @property
    def yet_not_created(self):
        if self.master_id:
            return False
        else:
            assert self.parent_id
            return True

    @property
    def parent_id(self):
        try:
            return self.caller.caller.master_id
        except AttributeError:
            if self.master_url:
                message = f'cannot find parent_id at: {self.master_url}'
            else:
                message = (f"ERROR: provide master_id or parent_id for this block;\n"
                           f"editor info:\n"
                           f"{self.unpack()}")
            raise AttributeError(message)

    def goto_last_children(self) -> SupportedBlock:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.children[-1]
        except IndexError:
            print('indentation not possible!')
            cursor = self
        return cursor

    def goto_parent(self) -> SupportedBlock:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.caller.master
        except AttributeError:
            print('exdentation not possible!')
            cursor = self
        return cursor

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def read_rich(self):
        pass

    @abstractmethod
    def unpack(self):
        return {'contents': "unpack contents here",
                'children': "unpack children here"}

    @abstractmethod
    def execute(self):
        """
        1. since self.children go first than self.new_children,
            assigning a multi-indented structure will be executed top to bottom,
            regardless of indentation.
        2. the 'ground editors', self.contents or self.props,
            have to refer to self.master_id if it want to 'reset gateway'.
            therefore, it first send the response without processing itself,
            so that the master deals with its reset task instead.
        """
        return


class BlockChildren(Editor):
    def __init__(self, caller: SupportedBlock):
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
            if child.has_children:
                child.children.fetch_descendants(page_size)

    def unpack(self):
        return {'children': self._normal.unpack(),
                'new_children': self._new.unpack()}

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
        try:
            cursor = self[-1].children
        except IndexError:
            print('indentation not possible!')
            cursor = self
        return cursor

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
    def __init__(self, caller: BlockChildren):
        super().__init__(caller)
        self.values: list[SupportedBlock] = []

    def __iter__(self):
        return self.values

    def apply_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            if not child_parser.is_supported_type:
                child = DefaultBlock(child_parser.block_id)
            else:
                if child_parser.is_page_block:
                    child = InlinePageBlock(child_parser.block_id)
                else:
                    child = TextBlock(child_parser.block_id)
                child.contents.apply_block_parser(child_parser)
            self.values.append(child)

    def reads(self):
        return [child.read for child in self]

    def reads_rich(self):
        return [child.read_rich for child in self]


class NewBlockChildrenContainer(BlockChildrenContainer):
    def __init__(self, caller: BlockChildren):
        self.caller = caller
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

    def unpack(self):
        return [request.unpack() for request in self._requests]

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
        child = TextBlock.create_new(self)
        if self._chunk_interrupted:
            self.gateway = AppendBlockChildren(self.caller.master_id)
            self._requests.append(self.gateway)
            self._chunks.append([])
            self._chunk_interrupted = False
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
        return self.gateway.apply_children(carrier)


class ContentsBlock(SupportedBlock, metaclass=ABCMeta):
    def __init__(self, block_id: str,
                 caller: Optional[BlockChildrenContainer] = None):
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

    def unpack(self):
        return {'contents': self.contents.unpack(),
                **self.children.unpack()}


class BlockContents(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: ContentsBlock):
        super().__init__(caller)
        self.gateway: Optional[UpdateBlock] = None
        self._read_plain = ''
        self._read_rich = []

    @abstractmethod
    def retrieve(self):
        pass

    def apply_block_parser(self, parser: BlockContentsParser):
        self.master_id = parser.block_id
        self.caller.has_children = parser.has_children
        self.caller.can_have_children = parser.can_have_children

        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich

    def read(self) -> str:
        return self._read_plain

    def read_rich(self) -> list:
        return self._read_rich


class TextBlock(ContentsBlock):
    def __init__(self, block_id: str,
                 caller: Optional[BlockChildrenContainer] = None):
        super().__init__(block_id, caller=caller)
        self.caller = caller
        self.contents = TextContents(self)
        self.agents.update(contents=self.contents)

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


class TextContents(BlockContents, TextContentsWriter):
    def __init__(self, caller: TextBlock):
        super().__init__(caller)
        self.caller = caller
        self.gateway = UpdateBlock(self.caller.master_id)

    def retrieve(self):
        gateway = RetrieveBlock(self.master_id)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        parser = BlockContentsParser.parse_update(response)
        self.apply_block_parser(parser)

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        if self.caller.yet_not_created:
            parent_block = self.caller.goto_parent()
            return parent_block.children.push_carrier(carrier)
        else:
            return self.gateway.apply_contents(carrier)


class InlinePageBlock(ContentsBlock):
    def __init__(self, page_id: str,
                 caller: Optional[NewBlockChildrenContainer] = None):
        super().__init__(page_id, caller)
        self.contents = InlinePageContents(self)
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


class InlinePageContents(BlockContents):
    def __init__(self, caller: InlinePageBlock):
        super().__init__(caller)
        self.caller = caller
        if self.caller.yet_not_created:
            self.gateway = CreatePage(self.caller.parent_id, under_database=False)
        else:
            self.gateway = UpdatePage(self.caller.master_id)

    def retrieve(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self.caller.yet_not_created:
            parser = PageParser.parse_create(response)
        else:
            parser = PageParser.parse_update(response)
        self.apply_page_parser(parser)

    def apply_page_parser(self, parser: PageParser):
        self.master_id = parser.page_id
        self.gateway = UpdatePage(self.master_id)
        self.caller.title = parser.title

        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def write(self, value: str):
        writer = self.write_rich()
        writer.write_text(value)
        return self.push_carrier(writer)

    def write_rich(self):
        writer = RichTextPropertyEncoder(prop_type='title', prop_name='title')
        pushed = self.push_carrier(writer)
        return pushed if pushed is not None else writer

    def push_carrier(self, carrier: RichTextPropertyEncoder) \
            -> Optional[RichTextPropertyEncoder]:
        if self.enable_overwrite or eval_empty(self.read()):
            return self.gateway.apply_prop(carrier)
        return None
