from ..common.pages import PagePayload
from .page_row import PageRow
from notion_zap.cli.gateway import encoders, requestors, parsers


class PageRowProperties(PagePayload, encoders.PageRowPropertyWriterbyKey):
    def __init__(self, caller: PageRow, id_or_url: str):
        PagePayload.__init__(self, caller, id_or_url)
        self.caller = caller
        self.frame = caller.frame
        if self.yet_not_created:
            self._requestor = requestors.CreatePage(self, under_database=True)
        else:
            self._requestor = requestors.UpdatePage(self)
        self._read_plain = {}
        self._read_rich = {}
        self._read_full = {}

    def clear_requestor(self):
        if self.yet_not_created:
            self._requestor = requestors.CreatePage(self, under_database=True)
        else:
            self._requestor = requestors.UpdatePage(self)

    @property
    def requestor(self):
        return self._requestor

    def apply_page_parser(self, parser: parsers.PageParser):
        super().apply_page_parser(parser)
        self.frame.fetch_parser(parser)
        self._set_title(parser.title)
        self._read_plain = parser.prop_values
        self._read_rich = parser.prop_rich_values
        for name in self._read_plain:
            if name in self._read_rich:
                value = {'plain': self._read_plain[name],
                         'rich': self._read_rich[name]}
            else:
                value = self._read_plain[name]
            self._read_full[name] = value

    def push_carrier(self, prop_key: str, carrier: encoders.PropertyEncoder) \
            -> encoders.PropertyEncoder:
        cannot_overwrite = (self.root.disable_overwrite and
                            not self.root.is_emptylike(self.read_of(prop_key)))
        # print(f"{self.read_of(prop_key)=},"
        #       f"{self.root.is_emptylike(self.read_of(prop_key))=}, "
        #       f"{cannot_overwrite=}")
        if cannot_overwrite:
            return carrier
        if prop_key == self.frame.title_key:
            self._set_title(carrier.plain_form())
        return self.requestor.apply_prop(carrier)

    def read_of(self, prop_key: str):
        self._assert_string_key(prop_key)
        try:
            value = self._read_plain[prop_key]
        except KeyError:
            raise KeyError(prop_key)
        return value

    def read_rich_of(self, prop_key: str):
        self._assert_string_key(prop_key)
        try:
            value = self._read_rich[prop_key]
        except KeyError:
            raise KeyError(prop_key)
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
        try:
            prop_key = self._name_at(prop_tag)
        except KeyError:
            return default
        return self.get_of(prop_key, default)

    def get_rich_at(self, prop_tag: str, default=None):
        try:
            prop_key = self._name_at(prop_tag)
        except KeyError:
            return default
        return self.get_rich_of(prop_key, default)

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
