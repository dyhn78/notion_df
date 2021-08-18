from typing import Optional, Any, Callable

from notion_py.gateway.common import ValueCarrier
from notion_py.gateway.others import RetrievePage
from notion_py.gateway.parse import PageParser
from notion_py.gateway.write import UpdatePage, PropertyUnitWriter

from notion_py.interface.edit.property_agent import TabularPropertyAgent
from notion_py.interface.edit.block import Block
from notion_py.interface.edit.common import EditorComponent
from notion_py.interface.frame import PropertyFrameDeprecated


class TabularPage(Block):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrameDeprecated] = None):
        super().__init__(page_id)
        self.props = TabularProperty(caller=self)
        self.components.update(props=self.props)

        self.frame = frame if frame is not None else PropertyFrameDeprecated()
        self.title = ''

    def fetch_retrieve(self):
        requestor = RetrievePage(self.head_id)
        response = requestor.execute()
        page_parser = PageParser.fetch_retrieve(response)

        self.props.fetch_page_parser(page_parser)
        self.title = page_parser.title
        return self.props


class TabularProperty(EditorComponent):
    write_manual = TabularPropertyAgent

    def __init__(self, caller: TabularPage):
        super().__init__(caller)
        self.frame = caller.frame
        self.agent = UpdatePage(caller.head_id)

        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def fetch_page_parser(self, page_parser: PageParser):
        self._read_plain = page_parser.props
        self._read_rich = page_parser.props_rich
        self._set_read_full()

    def _set_read_full(self):
        for prop_name in self._read_plain:
            if prop_name in self._read_rich:
                value = {'plain': self._read_plain[prop_name],
                         'rich': self._read_rich[prop_name]}
            else:
                value = self._read_plain[prop_name]
            self._read_full[prop_name] = value

    def _prop_name(self, key):
        return self.frame[key].name

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

    def write(self, prop_name: str, prop_value):
        prop_type = 'something'
        function: Callable[[str, Any], PropertyUnitWriter] \
            = getattr(self.write_manual, prop_type)
        carrier = function(prop_name, prop_value)
        self.pull_carrier(prop_name, carrier)

    def pull_carrier(self, prop_name: str, carrier: ValueCarrier):
        if self.enable_overwrite or self.eval_empty(self.read(prop_name)):
            self.agent.props.apply(carrier)

    @staticmethod
    def eval_empty(value):
        if type(value) in [bool, list, dict]:
            return bool(value)
        else:
            return str(value) in ['', '.', '-', '0', '1']
