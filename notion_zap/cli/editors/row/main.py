from __future__ import annotations
from typing import Union, Optional, Any, Hashable

from notion_zap.cli.structs import PropertyFrame
from ..shared.page import PageBlock
from notion_zap.cli.editors.structs.children import Children
from ..structs.base_logic import RootGatherer
from ...gateway import requestors, parsers
from ...gateway.encoders import (
    PageRowPropertyWriter,
    PropertyEncoder
)


class PageRow(PageBlock, PageRowPropertyWriter):
    def __init__(self, caller: Union[RootGatherer, Children],
                 id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        from ..database.main import RowChildren
        PageBlock.__init__(self, caller, id_or_url)
        self.caller: Union[RootGatherer, RowChildren] = caller

        self.frame = frame if frame else PropertyFrame()
        self._read_plain = {}
        self._read_rich = {}

        if self.parent:
            for key in self.parent.rows.by_keys:
                self.register_a_key(key)
            for key_alias in self.parent.rows.by_tags:
                self.register_a_tag(key_alias)

        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=True)

    @property
    def parent(self):
        from ..database.main import Database
        if parent := super().parent:
            assert isinstance(parent, Database)
            return parent
        return None

    def register_a_key(self, key: str):
        return self.regs.add(('key', key),
                      lambda x: x.block.get_key(key))

    def register_a_tag(self, key_alias: Hashable):
        return self.regs.add(('tag', key_alias),
                             lambda x: x.block.get_key_alias(key_alias))

    @property
    def requestor(self):
        return self._requestor

    def clear_requestor(self):
        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=True)

    def _apply_page_parser(self, parser: parsers.PageParser):
        super()._apply_page_parser(parser)
        self.frame.fetch_parser(parser)
        self._title = parser.pagerow_title
        self._read_plain = parser.values
        self._read_rich = parser.rich_values

    def push_encoder(self, key: str, encoder: PropertyEncoder) \
            -> PropertyEncoder:
        cannot_overwrite = (self.root.disable_overwrite and
                            self.root.eval(self.read_key(key)))
        if cannot_overwrite:
            return encoder
        # if key == self.frame.title_key:
        #     self._title = encoder.plain_form()
        return self.requestor.apply_prop(encoder)

    def read_key(self, key: str):
        self._assert_string_key(key)
        try:
            value = self._read_plain[key]
        except KeyError as e:
            # TODO
            from pprint import pprint
            pprint(self._read_plain)
            raise e
        return value

    def richly_read_key(self, key: str):
        self._assert_string_key(key)
        value = self._read_rich[key]
        return value

    def get_key(self, key: str, default=None):
        self._assert_string_key(key)
        value = self._read_plain.get(key)
        if value is None:
            value = default
        return value

    def richly_get_key(self, key: str, default=None):
        self._assert_string_key(key)
        value = self._read_rich.get(key)
        if value is None:
            value = default
        return value

    def read_key_alias(self, key_alias: Hashable):
        return self.read_key(self.frame.get_key(key_alias))

    def richly_read_key_alias(self, key_alias: Hashable):
        return self.richly_read_key(self.frame.get_key(key_alias))

    def get_key_alias(self, key_alias: Hashable, default=None):
        try:
            key = self.frame.get_key(key_alias)
        except KeyError:
            return default
        return self.get_key(key, default)

    def richly_get_key_alias(self, key_alias: Hashable, default=None):
        try:
            key = self.frame.get_key(key_alias)
        except KeyError:
            return default
        return self.richly_get_key(key, default)

    def read_all_keys(self):
        return self._read_plain

    def read_all_key_aliases(self):
        return {key: self._read_plain[self.frame.get_key(key)]
                for key in self.frame.key_aliases()}

    def richly_read_all_keys(self):
        return self._read_rich

    def richly_read_all_key_aliases(self):
        return {key: self._read_rich[self.frame.get_key(key)]
                for key in self.frame.key_aliases()}

    def read_contents(self) -> dict[str, Any]:
        """this method is purely built for trickle-down reading;
        don't use it editing source.
        only shows columns with manual tag."""
        return self.read_all_key_aliases()

    def richly_read_contents(self) -> dict[str, Any]:
        """this method is purely built for trickle-down reading;
        don't use it editing source.
        only shows columns with manual tag."""
        res = {}
        for tag in self.frame.key_aliases():
            if rich_value := self._read_rich.get(self.frame.get_key(tag)):
                res.update({tag: rich_value})
            else:
                plain_value = self._read_plain.get(self.frame.get_key(tag))
                res.update({tag: plain_value})
        return res

    @staticmethod
    def _assert_string_key(key: str):
        if not isinstance(key, str):
            comment = f"<key: {key}>"
            raise TypeError(comment)
        return
