from __future__ import annotations

from abc import abstractmethod, ABCMeta
from typing import Optional, Union

from notion_py.interface.struct.editor import GroundEditor, BridgeEditor, MasterEditor, \
    Editor
from .eval_empty import eval_empty
from ...api_format.encode import \
    BlockWriter, BlockContentsWriter, RichTextUnitWriter, PropertyUnitWriter
from ...api_format.parse import \
    BlockChildrenParser, BlockContentsParser, PageParser
from ...gateway import \
    RetrievePage, RetrieveBlock, GetBlockChildren, \
    UpdatePage, CreatePage, UpdateBlock, AppendBlockChildren
from ...utility import page_id_to_url


class DefaultBlock(MasterEditor):
    def __init__(self, block_id: str, caller: Optional[NewBlockChildren] = None):
        super().__init__(block_id, caller)
        self.is_supported_type = False
        self.can_have_children = False
        self.has_children = False

    def read(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported'}

    def read_rich(self) -> dict[str, Union[str, list]]:
        return {'type': 'unsupported'}

    def unpack(self):
        return {}

    def execute(self):
        return {}

    @property
    def master_url(self):
        return page_id_to_url(self.master_id)


class SupportedBlock(DefaultBlock):
    @abstractmethod
    def __init__(self, block_id: str,
                 caller: Optional[Union[BridgeEditor, NewBlockChildren]] = None):
        super().__init__(block_id, caller)
        self.is_supported_type = True
        self.can_have_children = True
        self.has_children = False

        self.children = NormalBlockChildren(self)
        self.new_children = NewBlockChildren(self)
        self.agents.update(children=self.children,
                           new_children=self.new_children)

    @classmethod
    def create_new(cls, caller: Union[BridgeEditor, NewBlockChildren]):
        return cls(block_id='', caller=caller)

    def get_children(self, page_size=0):
        gateway = GetBlockChildren(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = BlockChildrenParser(response)
        self.children.apply_parser(parser)

    def get_descendants(self, page_size=0):
        self.get_children(page_size)
        for child in self.new_children:
            if child.has_children:
                child.get_descendants()

    @property
    def is_yet_not_created(self):
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

    def list_all_children(self) -> list[SupportedBlock]:
        return self.children.values + self.new_children.values

    def goto_last_children(self) -> SupportedBlock:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.list_all_children()[-1]
        except IndexError:
            print('indentation not possible!')
            cursor = self
        return cursor

    def goto_parent(self) -> SupportedBlock:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = self.caller.caller
        except (AttributeError, AssertionError):
            print('exdentation not possible!')
            cursor = self
        return cursor

    @abstractmethod
    def retrieve_this(self):
        pass

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

    def _execute_children_agents(self):
        self.children.execute()
        new_values = self.new_children.execute()
        self.children.values.extend(new_values)


class ContentsBlock(SupportedBlock, metaclass=ABCMeta):
    def __init__(self, block_id: str, caller: Optional[NewBlockChildren] = None):
        super().__init__(block_id, caller)
        self.contents = None

    def apply_block_parser(self, parser: BlockContentsParser):
        """AppendBlockChildren request executed by parent_block"""
        if not self.master_id:
            self.master_id = parser.block_id
        self.has_children = parser.has_children
        self.can_have_children = parser.can_have_children
        self.contents.apply_block_parser(parser)

    def read(self):
        return {'contents': self.contents.read(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'contents': self.contents.read_rich(),
                'children': self.children.reads_rich()}

    def unpack(self):
        return {'contents': self.contents.unpack(),
                'children': self.children.unpack(),
                'new_children': self.new_children.unpack()}


class TextBlock(ContentsBlock):
    def __init__(self, block_id: str, caller: Optional[NewBlockChildren] = None):
        super().__init__(block_id, caller=caller)
        self.contents = TextBlockContents(self)
        self.agents.update(contents=self.contents)

    def retrieve_this(self):
        gateway = RetrieveBlock(self.master_id)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        response = self.contents.execute()
        parser = BlockContentsParser.parse_update(response)
        self.apply_block_parser(parser)
        if self.master_id:
            self.contents.reset_gateway()
        self._execute_children_agents()

    def read(self):
        return dict(**super().read(), type='text')

    def read_rich(self):
        return dict(**super().read(), type='text')


class InlinePageBlock(ContentsBlock):
    def __init__(self, page_id: str,
                 caller: Optional[NewBlockChildren] = None):
        super().__init__(page_id, caller)
        self.contents = InlinePageBlockContents(self)
        self.agents.update(contents=self.contents)
        self.title = ''

    def retrieve_this(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def apply_page_parser(self, parser: PageParser):
        self.title = parser.title
        self.contents.apply_page_parser(parser)

    def read(self):
        return dict(**super().read(), type='page')

    def read_rich(self):
        return dict(**super().read(), type='page')

    def execute(self):
        response = self.contents.execute()
        if self.master_id:
            parser = PageParser.parse_update(response)
            self.apply_page_parser(parser)
        else:
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
            self.master_id = parser.page_id
            self.new_children.gateway.parent_id = self.master_id
        self._execute_children_agents()


class BlockContents(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: MasterEditor):
        super().__init__(caller)
        self.gateway: Optional[UpdateBlock] = None
        self._read_plain = ''
        self._read_rich = []

    def apply_block_parser(self, child_parser: BlockContentsParser):
        self._read_plain = child_parser.read_plain
        self._read_rich = child_parser.read_rich

    def read(self) -> str:
        return self._read_plain

    def read_rich(self) -> list:
        return self._read_rich


class TextBlockContents(BlockContents, BlockContentsWriter):
    def __init__(self, caller: TextBlock):
        super().__init__(caller)
        assert isinstance(self.caller, TextBlock)
        if self.caller.is_yet_not_created:
            self.gateway = self.caller.goto_parent().new_children.gateway
            assert isinstance(self.gateway, AppendBlockChildren)
        else:
            self.gateway = self._default_gateway()

    def reset_gateway(self):
        self.gateway = self._default_gateway()

    def _default_gateway(self):
        return UpdateBlock(self.caller.master_id)

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        return self.gateway.apply_contents(carrier)


class InlinePageBlockContents(BlockContents):
    def __init__(self, caller: InlinePageBlock):
        super().__init__(caller)
        assert isinstance(self.caller, InlinePageBlock)
        if self.caller.is_yet_not_created:
            self.gateway = CreatePage(self.caller.parent_id, under_database=False)
        else:
            self.gateway = UpdatePage(self.caller.master_id)

    def apply_page_parser(self, parser: PageParser):
        if not self.gateway.page_id:
            self.gateway.page_id = parser.page_id
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def write(self, value: str):
        writer = self.write_rich()
        writer.write_text(value)
        return self._push(writer)

    def write_rich(self):
        writer = RichTextUnitWriter(prop_type='title', prop_name='title')
        pushed = self._push(writer)
        return pushed if pushed is not None else writer

    def _push(self, carrier: PropertyUnitWriter) \
            -> Optional[RichTextUnitWriter]:
        if self.enable_overwrite or eval_empty(self.read()):
            return self.gateway.apply_prop(carrier)
        return None


class NormalBlockChildren(BridgeEditor):
    def __init__(self, caller: SupportedBlock):
        super().__init__(caller)
        self.values: list[SupportedBlock] = []

    def apply_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            if not child_parser.is_supported_type:
                child = DefaultBlock(child_parser.block_id)
            else:
                if child_parser.is_page_block:
                    child = InlinePageBlock(child_parser.block_id)
                else:
                    child = TextBlock(child_parser.block_id)
                child.apply_block_parser(child_parser)
            self.values.append(child)

    def reads(self):
        return [child.read for child in self]

    def reads_rich(self):
        return [child.read_rich for child in self]


class NewBlockChildren(Editor):
    def __init__(self, caller: SupportedBlock):
        self.caller = caller
        self.requests: list[Union[AppendBlockChildren, InlinePageBlock]] = []
        self.values: list[ContentsBlock] = []

    def __iter__(self) -> list[ContentsBlock]:
        return self.values

    def __getitem__(self, index: int):
        return self.values[index]

    def __len__(self):
        return len(self.values)

    def __bool__(self):
        return any(child for child in self)

    def set_overwrite_option(self, option: bool):
        pass

    @property
    def gateway(self):
        return self.requests[-1]

    def add_gateway(self):
        gateway = AppendBlockChildren(self.caller.master_id)
        self.requests.append(gateway)
        return gateway

    def new_text_block(self):
        if not isinstance(self.gateway, AppendBlockChildren):
            self.add_gateway()
        child = TextBlock.create_new(self)
        self.values.append(child)
        # for debugging
        if id(child) != id(self.values[-1]):
            print('lol')
        return child

    def new_inline_page(self):
        child = InlinePageBlock.create_new(self)
        self.values.append(child)
        self.requests.append(child)
        # for debugging
        if id(child) != id(self.values[-1]):
            print('lol')
        return child

    def unpack(self):
        return [child.unpack() for child in self]

    def execute(self):
        children = iter(self.values)
        for request in self.requests:
            if isinstance(request, AppendBlockChildren):
                response = request.execute()
                parsers = BlockChildrenParser(response)
                for parser, new_child in zip(parsers, children):
                    new_child.apply_block_parser(parser)
            elif isinstance(request, InlinePageBlock):
                request.execute()
                next(children)
            else:
                raise ValueError('what did you do?!')
        res = self.values.copy()
        self.values.clear()
        self.requests.clear()
        return res

    def indent_next_block(self) -> NewBlockChildren:
        """if not possible, the cursor will stay at its position."""
        try:
            cursor = list(self)[-1].new_children
        except IndexError:
            print('indentation not possible!')
            cursor = self
        return cursor

    def exdent_next_block(self) -> NewBlockChildren:
        """if not possible, the cursor will stay at its position."""
        try:
            assert isinstance(self.caller, SupportedBlock)
            cursor = self.caller.caller
        except (AttributeError, AssertionError):
            print('exdentation not possible!')
            cursor = self
        return cursor
