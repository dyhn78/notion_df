from __future__ import annotations
from typing import Union, Optional, Any, Hashable

from notion_zap.cli.structs import PropertyFrame
from ..shared.page import PageBlock, PagePayload
from ..shared.with_children import Children
from ..structs.base_logic import RootGatherer
from ..structs.block_main import Payload
from ...gateway import encoders, requestors, parsers


class PageRow(PageBlock):
    def __init__(self, caller: Union[RootGatherer, Children],
                 id_or_url: str,
                 frame: Optional[PropertyFrame] = None):
        self.frame = frame if frame else PropertyFrame()
        PageBlock.__init__(self, caller, id_or_url)

        from ..database.main import RowChildren
        self.caller: Union[RootGatherer, RowChildren] = caller

    def _initalize_payload(self, block_id: str) -> Payload:
        return PageRowProperties(self, block_id)

    @property
    def payload(self) -> PageRowProperties:
        # noinspection PyTypeChecker
        return super(PageRow, self).payload

    @property
    def props(self) -> PageRowProperties:
        # noinspection PyTypeChecker
        return self.payload

    @property
    def parent(self):
        from ..database.main import Database
        if parent := super().parent:
            assert isinstance(parent, Database)
            return parent
        return None


class PageRowProperties(PagePayload, encoders.PageRowPropertyWriter):
    def __init__(self, caller: PageRow, block_id: str):
        self.frame = caller.frame if caller.frame else PropertyFrame()
        PagePayload.__init__(self, caller, block_id)
        encoders.PageRowPropertyWriter.__init__(self, self.frame)
        self.caller = caller

        if self.parent:
            for prop_key in self.parent.rows.by_keys:
                self.add_key_reg(prop_key)
            for prop_tag in self.parent.rows.by_tags:
                self.add_tag_reg(prop_tag)

        self._read_plain = {}
        self._read_rich = {}

        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=True)

    def add_key_reg(self, prop_key):
        self.regs.add(('key', prop_key),
                      lambda x: x.block.props.get_key(prop_key))

    def add_tag_reg(self, prop_tag):
        self.regs.add(('tag', prop_tag),
                      lambda x: x.block.props.get_key(prop_tag))

    @property
    def block(self) -> PageRow:
        return self.caller

    @property
    def requestor(self):
        return self._requestor

    def clear_requestor(self):
        if self.block_id:
            self._requestor = requestors.UpdatePage(self)
        else:
            self._requestor = requestors.CreatePage(self, under_database=True)

    def apply_page_parser(self, parser: parsers.PageParser):
        super().apply_page_parser(parser)
        self.frame.fetch_parser(parser)
        self._set_title(parser.pagerow_title)

        for reg in self.regs:
            if reg.track_key not in ['id', 'title']:
                reg.un_register_from_root_and_parent()
        self._read_plain = parser.values
        self._read_rich = parser.rich_values
        for reg in self.regs:
            if reg.track_key not in ['id', 'title']:
                reg.register_to_root_and_parent()

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

    def read_tag(self, prop_tag: Hashable):
        return self.read_key(self.frame.key_of(prop_tag))

    def richly_read_tag(self, prop_tag: Hashable):
        return self.richly_read_key(self.frame.key_of(prop_tag))

    def get_tag(self, prop_tag: Hashable, default=None):
        try:
            prop_key = self.frame.key_of(prop_tag)
        except KeyError:
            return default
        return self.get_key(prop_key, default)

    def richly_get_tag(self, prop_tag: Hashable, default=None):
        try:
            prop_key = self.frame.key_of(prop_tag)
        except KeyError:
            return default
        return self.richly_get_key(prop_key, default)

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

    @staticmethod
    def _assert_string_key(prop_key):
        if not isinstance(prop_key, str):
            comment = f"<prop_key: {prop_key}>"
            raise TypeError(comment)
        return
