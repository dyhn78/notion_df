from __future__ import annotations

from typing import Optional

from .block import Block
from .editor_struct import GatewayEditor, BridgeEditor
from .property_writer import TabularPropertybyKey
from ..frame import PropertyFrame
from ..parse import PageParser
from ...gateway.read import RetrievePage
from ...gateway.write import UpdatePage
from ...gateway.write.property import PropertyUnitWriter


class TabularPage(Block):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None,
                 caller: Optional[BridgeEditor] = None):
        super().__init__(page_id, caller=caller)
        self.props = TabularProperty(caller=self)
        self.agents.update(props=self.props)
        self.frame = frame if frame is not None else PropertyFrame()
        self.title = ''

    def fetch_retrieve(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        page_parser = PageParser.fetch_retrieve(response)

        self.props.fetch_parser(page_parser)
        self.title = page_parser.title
        return self.props


class TabularProperty(GatewayEditor, TabularPropertybyKey):
    def __init__(self, caller: TabularPage):
        super().__init__(caller)
        self.gateway = UpdatePage(caller.master_id)
        self.frame = caller.frame

        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def fetch_parser(self, page_parser: PageParser):
        self._read_plain = page_parser.props
        self._read_rich = page_parser.props_rich
        for prop_name, prop_type in page_parser.prop_types:
            frame_unit = self.frame.name_to_unit[prop_name]
            frame_unit.type = prop_type
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

    def read_all(self):
        return self._read_full

    def read_all_keys(self):
        return {key: self._read_full[self._prop_name(key)] for key in self.frame}

    def read(self, prop_name: str):
        return self._read_plain[prop_name]

    def read_rich(self, prop_name: str):
        return self._read_rich[prop_name]

    def read_on(self, prop_key: str):
        return self.read(self._prop_name(prop_key))

    def read_rich_on(self, prop_key: str):
        return self.read_rich(self._prop_name(prop_key))

    def _push(self, prop_name: str, carrier: PropertyUnitWriter) \
            -> Optional[PropertyUnitWriter]:
        if self.enable_overwrite or self.eval_empty(self.read(prop_name)):
            return self.gateway.props.apply(carrier)
        return None

    def _prop_name(self, prop_key: str):
        return self.frame.key_to_name[prop_key]

    def _prop_type(self, prop_name: str):
        return self.frame.name_to_unit[prop_name].type

    @staticmethod
    def eval_empty(value):
        if type(value) in [bool, list, dict]:
            return bool(value)
        else:
            return str(value) in ['', '.', '-', '0', '1']
