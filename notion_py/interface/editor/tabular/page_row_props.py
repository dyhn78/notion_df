from notion_py.interface.editor.common.pages import PagePayload
from notion_py.interface.encoder import PageRowPropertybyKey, PropertyEncoder
from notion_py.interface.parser import PageParser
from .page_row import PageRow
from ...requestor import CreatePage, UpdatePage
from ...utility import eval_empty


class PageRowProperty(PagePayload, PageRowPropertybyKey):
    def __init__(self, caller: PageRow):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame
        if self.yet_not_created:
            self._requestor = CreatePage(self, under_database=True)
        else:
            self._requestor = UpdatePage(self)
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    @property
    def requestor(self):
        return self._requestor

    @requestor.setter
    def requestor(self, value):
        self._requestor = value

    def apply_page_parser(self, parser: PageParser):
        super().apply_page_parser(parser)
        self.frame.fetch_parser(parser)
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
        writeable = self.root.enable_overwrite or eval_empty(self.read_of(prop_key))
        if not writeable:
            return carrier
        if prop_key == self.frame.title_key:
            self._set_title(carrier.plain_form())
        return self.requestor.apply_prop(carrier)

    def read_of(self, prop_key: str):
        self._assert_string_key(prop_key)
        try:
            value = self._read_plain[prop_key]
        except KeyError:
            raise KeyError(f"prop_key: {prop_key}")
        return value

    def read_rich_of(self, prop_key: str):
        self._assert_string_key(prop_key)
        try:
            value = self._read_rich[prop_key]
        except KeyError:
            raise KeyError(f"prop_key: {prop_key}")
        return value

    def get_of(self, prop_key: str, default=None):
        self._assert_string_key(prop_key)
        value = self._read_plain.get(prop_key)
        if value is None:
            value = default
        return value

    def get_rich_of(self, prop_key: str, default=None):
        self._assert_string_key(prop_key)
        value = self._read_rich.get(prop_key)
        if value is None:
            value = default
        return value

    def read_at(self, prop_tag: str):
        return self.read_of(self._name_at(prop_tag))

    def read_rich_at(self, prop_tag: str):
        return self.read_rich_of(self._name_at(prop_tag))

    def get_at(self, prop_tag: str, default=None):
        return self.get_of(self._name_at(prop_tag), default)

    def get_rich_at(self, prop_tag: str, default=None):
        return self.get_rich_of(self._name_at(prop_tag), default)

    @staticmethod
    def _assert_string_key(prop_key):
        if not isinstance(prop_key, str):
            comment = f"<prop_key: {prop_key}>"
            raise TypeError(comment)
        return

    def _name_at(self, prop_tag: str):
        return self.frame.key_at(prop_tag)

    def _type_of(self, prop_key: str):
        return self.frame.type_of(prop_key)

    def all_plain_keys(self):
        return self._read_plain

    def all_plain_tags(self):
        return {key: self._read_plain[self._name_at(key)]
                for key in self.frame.tags()}

    def all_rich_keys(self):
        return self._read_rich

    def all_keys(self):
        return self._read_full

    def all_tags(self):
        return {key: self._read_full[self._name_at(key)]
                for key in self.frame.tags()}


"""
class PageRowProperty(BlockEditor):
    def __init__(self, caller: BlockEditor):
        super().__init__(caller)
        self.caller = caller
        self.frame = caller.frame if hasattr(caller, 'frame') else PropertyFrame()
        self._container = TabularPropertyHandler(self)
        self._read_plain = {}
        self._read_rich = {}
        self._value_stash = {}
        self._type_stash = {}
        self.by_tag = {}

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
