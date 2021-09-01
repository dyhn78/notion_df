from __future__ import annotations

from abc import ABCMeta, abstractmethod
from typing import Optional, Union

from .eval_empty import eval_empty
from .struct import GroundEditor, BridgeEditor, MainEditor
from ...api_format.encode import \
    BlockWriter, BlockContentsWriter, RichTextUnitWriter, PropertyUnitWriter
from ...api_format.parse import \
    BlockChildrenParser, BlockContentsParser, PageParser
from ...gateway import \
    RetrievePage, RetrieveBlock, GetBlockChildren, \
    UpdatePage, CreatePage, UpdateBlock, AppendBlockChildren


class Block(MainEditor):
    def __init__(self, block_id: str, caller: Optional[BlockChildren] = None):
        super().__init__(block_id, caller)
        self.children = BlockChildren(self)
        self.agents.update(children=self.children)
        self.has_children = True
        self.can_have_children = True

    def fetch_children(self, page_size=0):
        gateway = GetBlockChildren(self.master_id)
        response = gateway.execute(page_size=page_size)
        parser = BlockChildrenParser(response)
        self.children.fetch_parser(parser)

    def fetch_descendants(self, page_size=0):
        self.fetch_children(page_size)
        for child in self.children:
            if child.has_children:
                child.fetch_descendants()

    def read(self):
        return {'type': 'unsupported',
                'contents': '',
                'children': self.children.read_list()}

    def read_rich(self):
        return {'type': 'unsupported',
                'contents': '',
                'children': self.children.read_rich_list()}


class InlineBlock(Block, metaclass=ABCMeta):
    @classmethod
    def create_new(cls, caller: BlockChildren):
        return cls(block_id='', caller=caller)

    @abstractmethod
    def fetch_retrieve(self):
        pass

    @abstractmethod
    def ack_update(self, response: dict):
        pass

    @abstractmethod
    def ack_create(self, response: dict):
        pass

    @abstractmethod
    def read(self):
        pass

    @abstractmethod
    def read_rich(self):
        pass


class InlineText(InlineBlock):
    def __init__(self, block_id: str, caller: Optional[BlockChildren] = None):
        super().__init__(block_id, caller=caller)
        self.contents = InlineTextContents(self)
        self.agents.update(contents=self.contents)

    def fetch_retrieve(self):
        gateway = RetrieveBlock(self.master_id)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.contents.fetch_parser(parser)

    def ack_update(self, response: dict):
        parser = BlockContentsParser.parse_update(response)
        self.contents.fetch_parser(parser)

    def ack_create(self, response_frag: dict):
        parser = BlockContentsParser.parse_create_frag(response_frag)
        self.contents.fetch_parser(parser)
        self.master_id = response_frag['id']

    def read(self):
        return {'type': 'text',
                'contents': self.contents.read(),
                'children': self.children.read_list()}

    def read_rich(self):
        return {'type': 'text',
                'contents': self.contents.read_rich(),
                'children': self.children.read_rich_list()}


class InlineTextContents(GroundEditor, BlockContentsWriter):
    def __init__(self, caller: InlineText):
        GroundEditor.__init__(self, caller)
        self.gateway = UpdateBlock(self.caller.master_id)
        self._read_plain = ''
        self._read_rich = []

    def fetch_parser(self, child_parser: BlockContentsParser):
        self._read_plain = child_parser.read_plain
        self._read_rich = child_parser.read_rich
        self.caller.has_children = child_parser.has_children
        self.caller.can_have_children = child_parser.can_have_children

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        return self.gateway.contents_apply(carrier)

    def read(self) -> str:
        return self._read_plain

    def read_rich(self) -> list:
        return self._read_rich


class InlinePage(InlineBlock):
    def __init__(self, page_id: str, caller: Optional[BlockChildren] = None):
        super().__init__(page_id, caller)
        gateway = self._set_proper_gateway()
        self.contents = InlinePageContents(
            caller=self, gateway=UpdatePage(gateway))
        self.agents.update(props=self.contents)
        self.title = ''

    def _set_proper_gateway(self):
        if self.master_id:
            gateway = UpdatePage(self.master_id)
        else:
            assert (parent_id := self.caller.caller.master_id)
            gateway = CreatePage(parent_id)
        return gateway

    def fetch_retrieve(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.contents.fetch_parser(parser)
        self.title = parser.title
        return self.contents

    def ack_update(self, response: dict):
        parser = PageParser.parse_update(response)
        self.contents.fetch_parser(parser)

    def ack_create(self, response: dict):
        parser = PageParser.parse_create(response)
        self.master_id = response['id']
        gateway = self._set_proper_gateway()
        self.contents = InlinePageContents(
            caller=self, gateway=UpdatePage(gateway))
        self.contents.fetch_parser(parser)

    def read(self):
        return {'type': 'page',
                'contents': self.contents.read(),
                'children': self.children.read_list()}

    def read_rich(self):
        return {'type': 'page',
                'contents': self.contents.read_rich(),
                'children': self.children.read_rich_list()}


class InlinePageContents(GroundEditor):
    def __init__(self, caller: InlinePage, gateway: Union[UpdatePage, CreatePage]):
        super().__init__(caller)
        self.gateway = gateway
        self._read_plain = {}
        self._read_rich = {}

    def fetch_parser(self, page_parser: PageParser):
        self._read_plain = page_parser.prop_values
        self._read_rich = page_parser.prop_rich_values

    def read(self):
        return self._read_plain['title']

    def read_rich(self):
        return self._read_rich['title']

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
    def __init__(self, caller: Block):
        BridgeEditor.__init__(self, caller)
        self.values: list[InlineBlock] = []  # BridgeEditor
        self.gateway = AppendBlockChildren(self.caller.master_id)
        self.new_values: list[InlineBlock] = []

    def __iter__(self) -> list[InlineBlock]:
        return self.values + self.new_values

    def _push(self, carrier: BlockWriter) -> BlockWriter:
        self.new_values.append(InlineText.create_new(self))
        return self.gateway.append_block(carrier)

    def execute(self):
        """
        since BridgeEditor go first, the recursive process will be shown
        top to bottom, regardless of indentation.
        """
        response = BridgeEditor.execute(self)
        for response_frag, child in zip(response['results'], self.values):
            child.ack_update(response_frag)

        response = GroundEditor.execute(self)
        for response_frag, new_child in zip(response['results'], self.new_values):
            new_child.ack_create(response_frag)
        self.values.extend(self.new_values)
        self.new_values = []

    def fetch_parser(self, children_parser: BlockChildrenParser):
        for child_parser in children_parser:
            if child_parser.is_page_block:
                child = InlinePage(child_parser.block_id)
            else:
                child = InlineText(child_parser.block_id)
            child.contents.fetch_parser(child_parser)
            self.values.append(child)

    def read_list(self):
        return [child.read for child in self]

    def read_rich_list(self):
        return [child.read_rich for child in self]

    def indent_next_block(self) -> BlockChildren:
        try:
            cursor = list(self)[-1].children
        except IndexError:
            print('indentation not available!')
            cursor = self
        return cursor

    def exdent_next_block(self) -> BlockChildren:
        try:
            assert isinstance(self.caller, Block)
            cursor = self.caller.caller
        except (AttributeError, AssertionError):
            print('exdentation not available!')
            cursor = self
        return cursor
