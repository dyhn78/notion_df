from notion_py.interface.api_encode import TabularPropertybyKey, PropertyEncoder
from notion_py.interface.api_parse import PageParser
from ...gateway import CreatePage, UpdatePage, RetrievePage
from ...struct import GroundEditor, PointEditor, PropertyFrame, drop_empty_request
from ...utility import eval_empty


class TabularProperty(GroundEditor, TabularPropertybyKey):
    def __init__(self, caller: PointEditor):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame if hasattr(caller, 'frame') else PropertyFrame()
        if not self.yet_not_created:
            gateway = UpdatePage(self)
        else:
            gateway = CreatePage(self, under_database=True)
        self.gateway = gateway
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def archive(self):
        self.gateway.archive()

    def un_archive(self):
        self.gateway.un_archive()

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
            self.apply_page_parser(parser)
        self.gateway = UpdatePage(self)

    def apply_page_parser(self, parser: PageParser):
        if parser.page_id:
            self.master_id = parser.page_id
        self.frame.fetch_parser(parser)
        self.caller.title = parser.title
        self.archived = parser.archived

        self._read_plain = parser.prop_values
        self._read_rich = parser.prop_rich_values
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

    def push_carrier(self, prop_key: str, carrier: PropertyEncoder) \
            -> PropertyEncoder:
        overwrite = self.enable_overwrite or eval_empty(self.read_of(prop_key))
        if overwrite:
            return self.gateway.apply_prop(carrier)
        else:
            return carrier

    def read_of_all(self):
        return self._read_plain

    def read_at_all(self):
        return {key: self._read_plain[self._name_at(key)]
                for key in self.frame.keys()}

    def read_rich_of_all(self):
        return self._read_rich

    def read_full_of_all(self):
        return self._read_full

    def read_full_at_all(self):
        return {key: self._read_full[self._name_at(key)]
                for key in self.frame.keys()}

    def read_of(self, prop_key: str):
        self._raise_if_nonstring_key(prop_key)
        try:
            value = self._read_plain[prop_key]
        except KeyError:
            raise KeyError(f"prop_key: {prop_key}")
        return value

    def read_rich_of(self, prop_key: str):
        self._raise_if_nonstring_key(prop_key)
        try:
            value = self._read_rich[prop_key]
        except KeyError:
            raise KeyError(f"prop_key: {prop_key}")
        return value

    def try_read_of(self, prop_key: str, default=None):
        self._raise_if_nonstring_key(prop_key)
        value = self._read_plain.get(prop_key)
        if value is None:
            value = default
        return value

    def try_read_rich_of(self, prop_key: str, default=None):
        self._raise_if_nonstring_key(prop_key)
        value = self._read_rich.get(prop_key)
        if value is None:
            value = default
        return value

    def read_at(self, prop_tag: str):
        return self.read_of(self._name_at(prop_tag))

    def try_read_at(self, prop_tag: str, default=None):
        return self.try_read_of(self._name_at(prop_tag), default)

    def read_rich_at(self, prop_tag: str):
        return self.read_rich_of(self._name_at(prop_tag))

    def try_read_rich_at(self, prop_tag: str, default=None):
        return self.try_read_rich_of(self._name_at(prop_tag), default)

    def _name_at(self, prop_tag: str):
        return self.frame.key_at(prop_tag)

    def _type_of(self, prop_key: str):
        return self.frame.type_of(prop_key)

    @staticmethod
    def _raise_if_nonstring_key(prop_key):
        if not isinstance(prop_key, str):
            comment = f"<prop_key: {prop_key}>"
            raise TypeError(comment)
        return


"""
class TabularProperty(PointEditor):
    def __init__(self, caller: PointEditor):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame if hasattr(caller, 'frame') else PropertyFrame()
        self._container = TabularPropertyHandler(self)
        self._read_plain = {}
        self._read_rich = {}
        self._value_stash = {}
        self._type_stash = {}
        self.by_key = {}

    def __getitem__(self, prop_key: str):
        return self._read_plain[prop_key]

    def __bool__(self):
        return any([bool(self._container), bool(self._value_stash)])

    def _encode(self):
        for prop_key, prop_value in self._value_stash.items():
            prop_type = self._type_stash.get(prop_key)
            self._container.write(prop_key, prop_value, prop_type)
        self._value_stash.clear()
"""