from typing import Optional

from ...api_format.encode import TabularPropertybyKey, PropertyEncoder
from ...api_format.parse import PageParser
from ...gateway import CreatePage, UpdatePage, RetrievePage
from ...struct import GroundEditor, Editor, PropertyFrame
from ...utility import eval_empty


class TabularProperty(Editor):
    def __init__(self, caller: Editor, callers_frame: PropertyFrame,
                 database_yet_not_created: bool,
                 database_id_if_page_yet_not_created=''):
        super().__init__(caller)
        self.caller = caller
        self.frame = callers_frame
        self._yet_not_created = bool(database_yet_not_created)
        self._container = \
            TabularPropertyContainer(self, self.frame,
                                     database_yet_not_created,
                                     database_id_if_page_yet_not_created)
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}
        self._value_stash = {}
        self._type_stash = {}

    def sync_master_id(self):
        self._container.sync_master_id()

    def sync_parent_id(self):
        self._container.sync_parent_id()

    def __getitem__(self, prop_name: str):
        return self._read_plain[prop_name]

    def __bool__(self):
        return any([bool(self._container), bool(self._value_stash)])

    def _encode(self):
        for prop_name, prop_value in self._value_stash.items():
            self._encode_unit(prop_name, prop_value)
        self._value_stash.clear()

    def _encode_unit(self, prop_name, prop_value):
        prop_type = self._type_stash.get(prop_name)
        self._container.write(prop_name, prop_value, prop_type)

    def read_all_plain(self):
        return self._read_plain

    def read_all_rich(self):
        return self._read_rich

    def read_all_at(self):
        return self._read_full

    def read_all_of(self):
        return {key: self._read_full[self._name_at(key)] for key in self.frame}

    def read_at(self, prop_name: str):
        return self._read_plain[prop_name]

    def read_rich_at(self, prop_name: str):
        return self._read_rich[prop_name]

    def read_of(self, prop_key: str):
        return self.read_at(self._name_at(prop_key))

    def read_rich_of(self, prop_key: str):
        return self.read_rich_at(self._name_at(prop_key))

    def _name_at(self, prop_key: str):
        return self.frame.by_key[prop_key].name

    def _type_of(self, prop_name: str):
        return self.frame.by_name[prop_name].type

    def retrieve_this(self):
        gateway = RetrievePage(self.master_id)
        response = gateway.execute()
        parser = PageParser.parse_retrieve(response)
        self._container.apply_page_parser(parser)

    def execute(self):
        return self._container.execute()

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


class TabularPropertyContainer(GroundEditor, TabularPropertybyKey):
    def __init__(self, caller: TabularProperty, callers_frame: PropertyFrame,
                 database_yet_not_created: bool,
                 database_id_if_not_yet_created=''):
        super().__init__(caller)
        self.caller = caller
        self.frame = callers_frame
        self._parent_yet_not_created = database_yet_not_created
        self._yet_not_created = \
            bool(database_id_if_not_yet_created) or self._parent_yet_not_created
        if self._yet_not_created:
            self.gateway = CreatePage(database_id_if_not_yet_created, under_database=True)
        else:
            self.gateway = UpdatePage(self.caller.master_id)
        self.read_plain = {}
        self.read_rich = {}
        self.read_full = {}

    def sync_parent_id(self):
        if self._parent_yet_not_created:
            self.gateway.target_id = self.master.caller.master_id

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
        self.frame.fetch_parser(parser)
        self.caller.title = parser.title

        self.read_plain = parser.prop_values
        self.read_rich = parser.prop_rich_values
        for name in self.read_plain:
            if name in self.read_rich:
                value = {'plain': self.read_plain[name],
                         'rich': self.read_rich[name]}
            else:
                value = self.read_plain[name]
            self.read_full[name] = value

    def push_carrier(self, prop_name: str, carrier: PropertyEncoder) \
            -> Optional[PropertyEncoder]:
        if self.enable_overwrite or eval_empty(self.read_at(prop_name)):
            return self.gateway.apply_prop(carrier)
        return None

    def read_all_plain(self):
        return self.read_plain

    def read_all_rich(self):
        return self.read_rich

    def read_all_at(self):
        return self.read_full

    def read_all_of(self):
        return {key: self.read_full[self._name_at(key)] for key in self.frame}

    def read_at(self, prop_name: str):
        return self.read_plain[prop_name]

    def read_rich_at(self, prop_name: str):
        return self.read_rich[prop_name]

    def read_of(self, prop_key: str):
        return self.read_at(self._name_at(prop_key))

    def read_rich_of(self, prop_key: str):
        return self.read_rich_at(self._name_at(prop_key))

    def _name_at(self, prop_key: str):
        return self.frame.by_key[prop_key].name

    def _type_of(self, prop_name: str):
        return self.frame.by_name[prop_name].type
