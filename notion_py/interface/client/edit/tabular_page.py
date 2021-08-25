from __future__ import annotations
from typing import Optional, Any, Callable, Union

from .block import Block
from .common import EditorComponent
from ..frame import PropertyFrame
from ..parse import PageParser
from ...common import ValueCarrier, DateFormat
from ...gateway.others import RetrievePage
from ...gateway.write import UpdatePage
from ...gateway.write.property import PropertyUnitWriter, RichTextUnitWriter, \
    SimpleUnitWriter


class TabularPage(Block):
    def __init__(self, page_id: str,
                 frame: Optional[PropertyFrame] = None):
        super().__init__(page_id)
        self.props = TabularProperty(caller=self)
        self.components.update(props=self.props)

        self.frame = frame if frame is not None else PropertyFrame()
        self.title = ''

    def fetch_retrieve(self):
        requestor = RetrievePage(self.target_id)
        response = requestor.execute()
        page_parser = PageParser.fetch_retrieve(response)

        self.props.fetch_parser(page_parser)
        self.title = page_parser.title
        return self.props


class TabularProperty(EditorComponent):
    def __init__(self, caller: TabularPage):
        super().__init__(caller)
        self.frame = caller.frame
        self.agent = UpdatePage(caller.target_id)
        self.writer = TabularPropertyWriter(self)

        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def fetch_parser(self, page_parser: PageParser):
        self._read_plain = page_parser.props
        self._read_rich = page_parser.props_rich
        for prop_name, prop_type in page_parser.prop_types:
            frame_unit = self.frame.name_to_unit[prop_name]
            frame_unit.type = prop_type
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
        return self.frame.key_to_name[key]

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

    def write(self, prop_name: str, prop_value, prop_type: Optional[str] = None):
        if not prop_type:
            prop_type = self.frame.name_to_unit[prop_name].type
        write_method: Callable[[str, Any], None] = getattr(self.writer, prop_type)
        write_method(prop_name, prop_value)

    def write_rich(self, prop_name: str, prop_type: Optional[str] = None):
        if not prop_type:
            prop_type = self.frame.name_to_unit[prop_name].type
        method_name = f'rich_{prop_type}'
        write_method: \
            Callable[[str], PropertyUnitWriter] = getattr(self.writer, method_name)
        carrier = write_method(prop_name)
        return carrier

    def fetch_carrier(self, prop_name: str, carrier: ValueCarrier):
        """will be called from TabularPropertyWriter"""
        if self.enable_overwrite or self.eval_empty(self.read(prop_name)):
            self.agent.props.apply(carrier)

    @staticmethod
    def eval_empty(value):
        if type(value) in [bool, list, dict]:
            return bool(value)
        else:
            return str(value) in ['', '.', '-', '0', '1']


class TabularPropertyWriter:
    def __init__(self, caller: TabularProperty):
        self.caller = caller

    def push(self, prop_name: str, carrier: PropertyUnitWriter):
        self.caller.fetch_carrier(prop_name, carrier)

    def rich_title(self, prop_name: str):
        writer = RichTextUnitWriter('title', prop_name)
        self.push(prop_name, writer)
        return writer

    def rich_text(self, prop_name: str):
        writer = RichTextUnitWriter('rich_text', prop_name)
        self.push(prop_name, writer)
        return writer

    def title(self, prop_name: str, value: str):
        self.push(prop_name, self.rich_title(prop_name).write_text(value))

    def text(self, prop_name: str, value: str):
        self.push(prop_name, self.rich_text(prop_name).write_text(value))

    def date(self, prop_name: str, value: DateFormat):
        self.push(prop_name, SimpleUnitWriter.date(prop_name, value))

    def url(self, prop_name: str, value: str):
        self.push(prop_name, SimpleUnitWriter.url(prop_name, value))

    def email(self, prop_name: str, value: str):
        self.push(prop_name, SimpleUnitWriter.email(prop_name, value))

    def phone_number(self, prop_name: str, value: str):
        self.push(prop_name, SimpleUnitWriter.phone_number(prop_name, value))

    def number(self, prop_name: str, value: Union[int, float]):
        self.push(prop_name, SimpleUnitWriter.number(prop_name, value))

    def checkbox(self, prop_name: str, value: bool):
        self.push(prop_name, SimpleUnitWriter.checkbox(prop_name, value))

    def select(self, prop_name: str, value: str):
        self.push(prop_name, SimpleUnitWriter.select(prop_name, value))

    def files(self, prop_name: str, value: str):
        self.push(prop_name, SimpleUnitWriter.files(prop_name, value))

    def people(self, prop_name: str, value: str):
        self.push(prop_name, SimpleUnitWriter.people(prop_name, value))

    def multi_select(self, prop_name: str, values: list[str]):
        self.push(prop_name, SimpleUnitWriter.multi_select(prop_name, values))

    def relation(self, prop_name: str, page_ids: list[str]):
        self.push(prop_name, SimpleUnitWriter.relation(prop_name, page_ids))
