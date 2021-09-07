from typing import Optional

from ...api_format.encode import TabularPropertybyKey, PropertyEncoder
from ...api_format.parse import PageParser
from ...gateway import CreatePage, UpdatePage, RetrievePage
from ...struct import GroundEditor, Editor, PropertyFrame, drop_empty_request
from ...utility import eval_empty


class TabularProperty(GroundEditor, TabularPropertybyKey):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame if hasattr(caller, 'frame') else PropertyFrame()
        if self.yet_not_created:
            self.gateway = CreatePage(self, under_database=True)
        else:
            self.gateway = UpdatePage(self)
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def retrieve(self):
        gateway = RetrievePage(self)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self.apply_page_parser(parser)

    @drop_empty_request
    def execute(self):
        response = self.gateway.execute()
        if self.yet_not_created:
            parser = PageParser.parse_create(response)
            self.gateway = UpdatePage(self)
        else:
            parser = PageParser.parse_update(response)
        self.apply_page_parser(parser)

    def apply_page_parser(self, parser: PageParser):
        self.master_id = parser.page_id
        self.frame.fetch_parser(parser)
        self.caller.title = parser.title

        self._read_plain = parser.prop_values
        self._read_rich = parser.prop_rich_values
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

    def push_carrier(self, prop_name: str, carrier: PropertyEncoder) \
            -> Optional[PropertyEncoder]:
        if self.enable_overwrite or eval_empty(self.read_at(prop_name)):
            return self.gateway.apply_prop(carrier)
        return None

    def read_at_all(self):
        return self._read_plain

    def read_rich_at_all(self):
        return self._read_rich

    def read_full_at_all(self):
        return self._read_full

    def read_full_of_all(self):
        return {key: self._read_full[self._name_at(key)] for key in self.frame}

    def read_of(self, prop_name: str):
        return self._read_plain[prop_name]

    def read_rich_of(self, prop_name: str):
        return self._read_rich[prop_name]

    def read_at(self, prop_key: str):
        return self.read_of(self._name_at(prop_key))

    def read_rich_at(self, prop_key: str):
        return self.read_rich_of(self._name_at(prop_key))

    def _name_at(self, prop_key: str):
        return self.frame.by_key[prop_key].name

    def _type_of(self, prop_name: str):
        return self.frame.by_name[prop_name].type


"""
class TabularProperty(Editor):
    def __init__(self, caller: Editor):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame if hasattr(caller, 'frame') else PropertyFrame()
        self._container = TabularPropertyHandler(self)
        self._read_plain = {}
        self._read_rich = {}
        self._value_stash = {}
        self._type_stash = {}
        self.by_key = {}

    def __getitem__(self, prop_name: str):
        return self._read_plain[prop_name]

    def __bool__(self):
        return any([bool(self._container), bool(self._value_stash)])

    def _encode(self):
        for prop_name, prop_value in self._value_stash.items():
            prop_type = self._type_stash.get(prop_name)
            self._container.write(prop_name, prop_value, prop_type)
        self._value_stash.clear()
"""