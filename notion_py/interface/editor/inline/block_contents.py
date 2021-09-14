from abc import ABCMeta, abstractmethod
from typing import Optional

from notion_py.interface.api_encode import \
    TextContentsWriter, RichTextContentsEncoder, \
    PageContentsWriterAsChildBlock, PageContentsWriterAsIndepPage, \
    RichTextPropertyEncoder
from notion_py.interface.api_parse import BlockContentsParser, PageParser
from ...gateway import UpdateBlock, RetrieveBlock, UpdatePage, RetrievePage, CreatePage
from ...struct import PointEditor, GroundEditor
from ...utility import eval_empty


class BlockContents(GroundEditor, metaclass=ABCMeta):
    def __init__(self, caller: PointEditor):
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
    def __init__(self, caller: PointEditor, uncle: Optional[GroundEditor] = None):
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


class PageContentsAsIndepPage(BlockContents, PageContentsWriterAsIndepPage):
    def __init__(self, caller: PointEditor):
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

    def push_carrier(self, carrier: RichTextPropertyEncoder) \
            -> Optional[RichTextPropertyEncoder]:
        overwrite = self.enable_overwrite or eval_empty(self.read())
        if overwrite:
            return self.gateway.apply_prop(carrier)
        else:
            return carrier


class PageContentsAsChildBlock(BlockContents, PageContentsWriterAsChildBlock):
    def __init__(self, caller: PointEditor, uncle: Optional[GroundEditor] = None):
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

    def push_carrier(self, carrier: RichTextContentsEncoder) \
            -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)
