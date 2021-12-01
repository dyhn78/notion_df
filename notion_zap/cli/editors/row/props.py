from typing import Any

from ..common.page import PagePayload
from .leader import PageRow
from notion_zap.cli.gateway import encoders, requestors, parsers
from notion_zap.cli.structs import PropertyFrame


class PageRowProperties(PagePayload, encoders.PageRowPropertyWriter):
    def __init__(self, caller: PageRow, id_or_url: str):
        PagePayload.__init__(self, caller)
        self.caller = caller
        self.frame: PropertyFrame = caller.frame
        encoders.PageRowPropertyWriter.__init__(self, self.frame)
        if id_or_url:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=True)
        self._read_plain = {}
        self._read_rich = {}

    def clear_requestor(self):
        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=True)

    @property
    def requestor(self):
        return self._requestor

    def apply_page_parser(self, parser: parsers.PageParser):
        super().apply_page_parser(parser)
        self.frame.fetch_parser(parser)
        self._set_title(parser.pagerow_title)
        self._read_plain = parser.values
        self._read_rich = parser.rich_values

    def push_encoder(self, prop_key: str, encoder: encoders.PropertyEncoder) \
            -> encoders.PropertyEncoder:
        cannot_overwrite = (self.root.disable_overwrite and
                            not self.root.count_as_empty(self.read_key(prop_key)))
        if cannot_overwrite:
            return encoder
        if prop_key == self.frame.title_key:
            self._set_title(encoder.plain_form())
        return self.requestor.apply_prop(encoder)

    def read_key(self, prop_key: str):
        self._assert_string_key(prop_key)
        try:
            value = self._read_plain[prop_key]
        except KeyError:
            raise KeyError(prop_key)
        return value

    def richly_read_key(self, prop_key: str):
        self._assert_string_key(prop_key)
        try:
            value = self._read_rich[prop_key]
        except KeyError:
            raise KeyError(prop_key)
        return value

    def get_key(self, prop_key: str, default=None):
        self._assert_string_key(prop_key)
        value = self._read_plain.get(prop_key)
        if value is None:
            value = default
        return value

    def richly_get_key(self, prop_key: str, default=None):
        self._assert_string_key(prop_key)
        value = self._read_rich.get(prop_key)
        if value is None:
            value = default
        return value

    def read_tag(self, prop_tag: str):
        return self.read_key(self.frame.key_of(prop_tag))

    def richly_read_tag(self, prop_tag: str):
        return self.richly_read_key(self.frame.key_of(prop_tag))

    def get_tag(self, prop_tag: str, default=None):
        try:
            prop_key = self.frame.key_of(prop_tag)
        except KeyError:
            return default
        return self.get_key(prop_key, default)

    def richly_get_tag(self, prop_tag: str, default=None):
        try:
            prop_key = self.frame.key_of(prop_tag)
        except KeyError:
            return default
        return self.richly_get_key(prop_key, default)

    @staticmethod
    def _assert_string_key(prop_key):
        if not isinstance(prop_key, str):
            comment = f"<prop_key: {prop_key}>"
            raise TypeError(comment)
        return

    def read_all_keys(self):
        return self._read_plain

    def read_all_tags(self):
        return {key: self._read_plain[self.frame.key_of(key)]
                for key in self.frame.tags()}

    def richly_read_all_keys(self):
        return self._read_rich

    def richly_read_all_tags(self):
        return {key: self._read_rich[self.frame.key_of(key)]
                for key in self.frame.tags()}

    def read(self) -> dict[str, Any]:
        """this method is purely built for trickle-down reading;
        don't use it editing source.
        only shows columns with manual tag."""
        return self.read_all_tags()

    def richly_read(self) -> dict[str, Any]:
        """this method is purely built for trickle-down reading;
        don't use it editing source.
        only shows columns with manual tag."""
        res = {}
        for tag in self.frame.tags():
            if rich_value := self._read_rich.get(self.frame.key_of(tag)):
                res.update({tag: rich_value})
            else:
                plain_value = self._read_plain.get(self.frame.key_of(tag))
                res.update({tag: plain_value})
        return res
