from abc import ABCMeta, abstractmethod
from typing import Optional

from ...api_format.encode import TextContentsWriter, RichTextContentsEncoder, \
    RichTextPropertyEncoder
from ...api_format.parse import BlockContentsParser, PageParser
from ...gateway import UpdateBlock, RetrieveBlock, CreatePage, UpdatePage, RetrievePage, \
    AppendBlockChildren
from ...struct import GroundEditor, Editor
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
    def __init__(self, caller: Editor,
                 gateway_alternative: Optional[AppendBlockChildren] = None):
        super().__init__(caller)
        self.caller = caller
        self.gateway = UpdateBlock(self.caller.master_id) \
            if gateway_alternative is None else gateway_alternative

    def retrieve(self):
        gateway = RetrieveBlock(self.master_id)
        response = gateway.execute()
        parser = BlockContentsParser.parse_retrieve(response)
        self.apply_block_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        parser = BlockContentsParser.parse_update(response)
        self.apply_block_parser(parser)
        self.reset_gateway()

    def reset_gateway(self):
        self.gateway = UpdateBlock(self.caller.master_id)

    def push_carrier(self, carrier: RichTextContentsEncoder) -> RichTextContentsEncoder:
        return self.gateway.apply_contents(carrier)


class InlinePageContents(BlockContents):
    def __init__(self, caller: Editor, parent_id_if_yet_not_created=''):
        super().__init__(caller)
        self.caller = caller
        self._yet_not_created = bool(parent_id_if_yet_not_created)
        if self._yet_not_created:
            self.gateway = CreatePage(parent_id_if_yet_not_created, under_database=False)
        else:
            self.gateway = UpdatePage(self.caller.master_id)

    def retrieve(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    def execute(self):
        response = self.gateway.execute()
        if self._yet_not_created:
            parser = PageParser.parse_create(response)
        else:
            parser = PageParser.parse_update(response)
        self.apply_page_parser(parser)
        if self._yet_not_created:
            self._yet_not_created = False
            self.gateway = UpdatePage(self.master_id)

    def apply_page_parser(self, parser: PageParser):
        self.master_id = parser.page_id
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
