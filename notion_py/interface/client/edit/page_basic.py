from typing import Optional

from .block import Block
from .editor_struct import GatewayEditor, BridgeEditor
from .page_tabular import TabularProperty
from ..parse import PageParser
from ...gateway.read import RetrievePage
from ...gateway.write import UpdatePage
from ...gateway.write.property import BasicPageTitleWriter, RichTextUnitWriter, \
    PropertyUnitWriter


class BasicPage(Block):
    def __init__(self, page_id: str,
                 caller: Optional[BridgeEditor] = None):
        super().__init__(page_id, caller=caller)
        self.props = BasicPageProperty(caller=self)
        self.agents.update(props=self.props)
        self.title = ''

    def fetch_retrieve(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        page_parser = PageParser.fetch_retrieve(response)

        self.props.fetch_parser(page_parser)
        self.title = page_parser.title
        return self.props


class BasicPageProperty(GatewayEditor):
    def __init__(self, caller: BasicPage):
        super().__init__(caller)
        self.gateway = UpdatePage(caller.master_id)

        self._read_plain = {}
        self._read_rich = {}

    def fetch_parser(self, page_parser: PageParser):
        self._read_plain = page_parser.props
        self._read_rich = page_parser.props_rich

    def read_rich_title(self):
        return self._read_rich['title']

    def read_title(self):
        return self._read_plain['title']

    def write_rich_title(self):
        writer = RichTextUnitWriter(value_type='title', prop_name='title')
        pushed = self._push(writer)
        return pushed if pushed is not None else writer

    def write_title(self, value: str):
        writer = self.write_rich_title()
        writer.write_text(value)
        return self._push(writer)

    def _push(self, carrier: PropertyUnitWriter) \
            -> Optional[RichTextUnitWriter]:
        if self.enable_overwrite or self.eval_empty(self.read_title()):
            return self.gateway.props.apply(carrier)
        return None

    @staticmethod
    def eval_empty(value):
        return TabularProperty.eval_empty(value)


class BasicPropertyAgent:
    @classmethod
    def write_rich_title(cls):
        return BasicPageTitleWriter('title')

    @classmethod
    def write_title(cls, value: str):
        return cls.write_rich_title().write_text(value)
