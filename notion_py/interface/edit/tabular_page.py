from typing import Optional, Any

from notion_py.gateway.others import RetrievePage
from notion_py.gateway.write import UpdatePage
from .common import EditorComponent
from .block import Block
from .tabular_property_agent import PlainPropertyAgent, RichPropertyAgent
from ..preset import PropertyFrame
from ..parse import PageParser
from ...gateway.common import ValueCarrier


class TabularPage(Block):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(page_id)
        self.frame = frame if frame is not None else PropertyFrame()
        self.props = None
        self.title = ''

    def fetch_retrieve(self):
        requestor = RetrievePage(self.head_id)
        response = requestor.execute()
        page_parser = PageParser.fetch_retrieve(response)
        self.fetch_page_parser(page_parser)
        return self.props

    def fetch_page_parser(self, page_parser: PageParser):
        self.props = TabularPageProps(caller=self,
                                      read_plain=page_parser.props,
                                      read_rich=page_parser.props_rich)
        self.components.update(props=self.props)
        self.title = page_parser.title


class TabularPageProps(EditorComponent):
    def __init__(self, caller: TabularPage,
                 read_plain: Optional[dict[str, Any]] = None,
                 read_rich: Optional[dict[str, Any]] = None):
        super().__init__(caller)
        self.frame = caller.frame
        self.agent = UpdatePage(caller.head_id)

        self._read_rich = read_rich
        self._read_plain = read_plain

        self._read_full = {}
        for prop_name in read_plain:
            if prop_name in read_rich:
                value = {'plain': read_plain[prop_name],
                         'rich': read_rich[prop_name]}
            else:
                value = read_plain[prop_name]
            self._read_full[prop_name] = value

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

    def write(self, prop_name: str):
        return PlainPropertyAgent(self, prop_name)

    def write_rich(self, prop_name: str):
        return RichPropertyAgent(self, prop_name)

    def write_on(self, prop_key: str):
        return self.write(self._prop_name(prop_key))

    def write_rich_on(self, prop_key: str):
        return self.write_rich(self._prop_name(prop_key))

    def _prop_name(self, key):
        return self.frame[key].name

    def apply(self, prop_name: str, carrier: ValueCarrier):
        if self.enable_overwrite:
            proceed = True
        else:
            proceed = self.eval_empty(self.read(prop_name))

        if proceed:
            self.agent.props.apply(carrier)

    @staticmethod
    def eval_empty(value):
        if type(value) in [bool, list, dict]:
            return bool(value)
        else:
            return str(value) in ['', '.', '-', '0', '1']
