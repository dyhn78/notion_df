from __future__ import annotations

from abc import abstractmethod, ABC, ABCMeta
from typing import Optional, Union

from .eval_empty import eval_empty
from notion_py.interface.struct.editor import GroundEditor, BridgeEditor, MasterEditor
from ...api_format.encode import \
    BlockWriter, BlockContentsWriter, RichTextUnitWriter, PropertyUnitWriter
from ...api_format.parse import \
    BlockChildrenParser, BlockContentsParser, PageParser
from ...gateway import \
    RetrievePage, RetrieveBlock, GetBlockChildren, \
    UpdatePage, CreatePage, UpdateBlock, AppendBlockChildren
from ...utility import page_id_to_url


class DefaultBlock(MasterEditor):
    def __init__(self, block_id: str, caller: Optional[BlockChildren] = None):
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
    def __init__(self, block_id: str, caller: Optional[BridgeEditor] = None):
        super().__init__(block_id, caller)
        self.children = None
        self.is_supported_type = True
        self.can_have_children = True
        self.has_children = False

    @classmethod
    def create_new(cls, caller: BlockChildren):
        return cls(block_id='', caller=caller)

    @abstractmethod
    def retrieve_this(self):
        pass

    def get_children(self, page_size=0):
        gateway = GetBlockChildren(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = BlockChildrenParser(response)
        self.children.apply_parser(parser)

    def get_descendants(self, page_size=0):
        self.get_children(page_size)
        for child in self.children:
            if child.is_supported_type:
                child.retrieve_this()
            if child.has_children:
                child.get_descendants()

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def read_rich(self):
        pass

    @abstractmethod
    def unpack(self):
        return {'contents': "unpack contents",
                'children': "unpack children"}

    @abstractmethod
    def execute(self):
        """
        * execute contents
        * execute children
        """
        return


class ContentsBlock(SupportedBlock, metaclass=ABCMeta):
    def __init__(self, block_id: str, caller: Optional[BlockChildren] = None):
        super().__init__(block_id, caller)
        self.contents = None

    def apply_block_parser(self, parser: BlockContentsParser):
        """AppendBlockChildren request executed by parent_block"""
        if not self.master_id:
            self.master_id = parser.block_id
        self.has_children = parser.has_children
        self.can_have_children = parser.can_have_children
        self.contents.apply_block_parser(parser)


class TextBlock(ContentsBlock):
    def __init__(self, block_id: str, caller: Optional[BlockChildren] = None):
        super().__init__(block_id, caller=caller)
        self.contents = TextBlockContents(self)
        self.agents.update(contents=self.contents)
        self.children = BlockChildren(self)
        self.agents.update(children=self.children)

    def retrieve_this(self):
        gateway = RetrieveBlock(self.master_id)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def read(self):
        return {'type': 'text',
                'contents': self.contents.read(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'type': 'text',
                'contents': self.contents.read_rich(),
                'children': self.children.reads_rich()}

    def unpack(self):
        return {'contents': self.contents.unpack(),
                'children': self.children.unpack()}

    def execute(self):
        # self.children will do the job of updating children_blocks.
        response = self.contents.execute()
        parser = BlockContentsParser.parse_update(response)
        self.apply_block_parser(parser)
        self.children.execute()


class InlinePageBlock(ContentsBlock):
    def __init__(self, page_id: str, caller: Optional[BlockChildren] = None):
        super().__init__(page_id, caller)
        self.contents = InlinePageBlockContents(self)
        self.children = BlockChildren(self)
        self.agents.update(contents=self.contents,
                           children=self.children)
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
        return {'type': 'page',
                'contents': self.contents.read(),
                'children': self.children.reads()}

    def read_rich(self):
        return {'type': 'page',
                'contents': self.contents.read_rich(),
                'children': self.children.reads_rich()}

    def unpack(self):
        return {'contents': self.contents.unpack(),
                'children': self.children.unpack()}

    def execute(self):
        resp_contents = self.contents.execute()
        parser = PageParser.parse_create(resp_contents)
        self.apply_page_parser(parser)
        if not self.master_id:
            self.master_id = parser.page_id
            self.children.gateway.parent_id = self.master_id
        self.children.execute()

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
                message = (f"ERROR: provide master_id or parent_id for the pageblock;\n"
                           f"editor info:\n"
                           f"{self.unpack()}")
            raise AttributeError(message)


class BlockContents(ABC):
    def __init__(self):
        self.gateway = None
        self._read_plain = ''
        self._read_rich = []

    def apply_block_parser(self, child_parser: BlockContentsParser):
        self._read_plain = child_parser.read_plain
        self._read_rich = child_parser.read_rich

    def read(self) -> str:
        return self._read_plain

    def read_rich(self) -> list:
        return self._read_rich


class TextBlockContents(GroundEditor, BlockContentsWriter, BlockContents):
    def __init__(self, caller: TextBlock):
        GroundEditor.__init__(self, caller)
        BlockContents.__init__(self)
        self.gateway = UpdateBlock(self.caller.master_id)

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        return self.gateway.apply_contents(carrier)


class InlinePageBlockContents(GroundEditor, BlockContents):
    def __init__(self, caller: InlinePageBlock):
        GroundEditor.__init__(self, caller)
        BlockContents.__init__(self)
        assert isinstance(self.caller, InlinePageBlock)
        if self.caller.is_yet_not_created:
            self.gateway = UpdatePage(self.caller.master_id)
        else:
            self.gateway = CreatePage(self.caller.parent_id)
        self._read_plain = ''
        self._read_rich = []

    def apply_page_parser(self, parser: PageParser):
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


class BlockChildren(BridgeEditor, GroundEditor, BlockContentsWriter):
    def __init__(self, caller: SupportedBlock):
        # UpdateBlock, one by one
        BridgeEditor.__init__(self, caller)
        self.values: list[SupportedBlock] = []

        # AppendBlockChildren, all at once
        self.gateway = AppendBlockChildren(self.caller.master_id)
        self.new_values: list[ContentsBlock] = []

    def __iter__(self) -> list[SupportedBlock]:
        return self.values + self.new_values

    def apply_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            if child_parser.is_page_block:
                child = InlinePageBlock(child_parser.block_id)

            elif child_parser.is_supported_type:
                child = TextBlock(child_parser.block_id)
                child.apply_block_parser(child_parser)
            else:
                child = DefaultBlock(child_parser.block_id)
            self.values.append(child)

    def execute(self):
        """
        since BridgeEditor go first, assigning a multilayer page will be
        executed top to bottom, regardless of indentation.
        """
        # existing child blocks will gather for themselves.
        BridgeEditor.execute(self)
        # however, new blocks need to be updated by parent.
        response = GroundEditor.execute(self)
        parsers = BlockChildrenParser(response)
        for parser, new_child in zip(parsers, self.new_values):
            new_child.apply_block_parser(parser)
        self.values.extend(self.new_values)
        self.new_values = []

    def reads(self):
        return [child.read for child in self]

    def reads_rich(self):
        return [child.read_rich for child in self]

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        self.new_values.append(TextBlock.create_new(self))
        return self.gateway.append_block(carrier)

    def indent_next_block(self) -> BlockChildren:
        try:
            cursor = list(self)[-1].children
        except IndexError:
            print('indentation not available!')
            cursor = self
        return cursor

    def exdent_next_block(self) -> BlockChildren:
        try:
            assert isinstance(self.caller, SupportedBlock)
            cursor = self.caller.caller
        except (AttributeError, AssertionError):
            print('exdentation not available!')
            cursor = self
        return cursor
