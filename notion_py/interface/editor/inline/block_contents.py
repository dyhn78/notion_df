from abc import ABCMeta, abstractmethod
from typing import Optional

from ...api_format.encode import TextContentsWriter, RichTextContentsEncoder, \
    PropertyEncoder
from ...api_format.encode.block_contents import InlinePageContentsWriter
from ...api_format.parse import BlockContentsParser, PageParser
from ...gateway import UpdateBlock, RetrieveBlock, UpdatePage, RetrievePage, CreatePage
from ...struct import Editor, GroundEditor
from ...utility import eval_empty


class BlockContents(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self.gateway: Optional[UpdateBlock] = None
        self._read_plain = ''
        self._read_rich = []

    @abstractmethod
    def retrieve(self):
        pass

    def apply_block_parser(self, parser: BlockContentsParser):
        if parser.block_id:
            self.master_id = parser.block_id
        self.caller.has_children = parser.has_children
        self.caller.can_have_children = parser.can_have_children
        self._read_plain = parser.read_plain
        self._read_rich = parser.read_rich

    def read(self) -> str:
        return self._read_plain

    def read_rich(self) -> list:
        return self._read_rich


class TextContents(BlockContents, TextContentsWriter):
    def __init__(self, caller: Editor, uncle: Optional[GroundEditor] = None):
        super().__init__(caller)
        self.caller = caller
        self.uncle = uncle
        self._gateway = UpdateBlock(self)

    @property
    def gateway(self):
        if self.uncle is not None:
            return self.uncle.gateway
        else:
            return self._gateway

    @gateway.setter
    def gateway(self, value):
        self._gateway = value

    def retrieve(self):
        gateway = RetrieveBlock(self)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        self.gateway.execute()

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)

"""
class InlinePageContents(BlockContents, InlinePageContentsWriter):
    def __init__(self, caller: Editor, uncle: Optional[GroundEditor] = None):
        super().__init__(caller)
        self.caller = caller
        self.uncle = uncle
        self._gateway = UpdateBlock(self)

    @property
    def gateway(self):
        if self.uncle is not None:
            return self.uncle.gateway
        else:
            return self._gateway

    @gateway.setter
    def gateway(self, value):
        self._gateway = value

    def retrieve(self):
        gateway = RetrievePage(self)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self.yet_not_created:
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
            self.gateway = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
        self.caller.title = parser.title
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)

"""
class InlinePageContents(BlockContents):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self.caller = caller
        if self.yet_not_created:
            self.gateway = CreatePage(self, under_database=False)
        else:
            self.gateway = UpdatePage(self)

    def retrieve(self):
        gateway = RetrievePage(self)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self.yet_not_created:
            parser = PageParser.parse_create(response)
            self.apply_page_parser(parser)
            self.gateway = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
        self.caller.title = parser.title
        self._read_plain = parser.prop_values['title']
        self._read_rich = parser.prop_rich_values['title']

    def write_title(self, value: str):
        writer = self.write_rich_title()
        writer.write_text(value)
        return writer

    def write_rich_title(self):
        writer = RichTextContentsEncoder('title')
        pushed = self.push_carrier(writer)
        return pushed if pushed is not None else writer

    def push_carrier(self, carrier: PropertyEncoder) \
            -> Optional[PropertyEncoder]:
        if self.enable_overwrite or eval_empty(self.read()):
            return self.gateway.apply_prop(carrier)
        return None
