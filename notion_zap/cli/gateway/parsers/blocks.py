from __future__ import annotations

import datetime as dt

from .rich_text import parse_rich_texts
from ...structs.base_logic import Printable
from ...structs.block_types import (
    PAGE_TYPES, TEXT_TYPES, CAN_HAVE_CHILDREN, SUPPORTED,
    UNSUPPORTED
)


class BlockChildrenParser:
    def __init__(self, response: dict):
        try:
            self.values: list[BlockContentsParser] = self._parse(response['results'])
        except KeyError:
            self.values: list[BlockContentsParser] = self._parse([response])

    @staticmethod
    def _parse(response_frag):
        return [BlockContentsParser.parse_retrieve_frag(rich_block_object)
                for rich_block_object in response_frag]

    def __iter__(self):
        return iter(self.values)


class BlockContentsParser(Printable):
    def __init__(
            self, block_id: str, block_type: str,
            created_time: dt.datetime, last_edited_time: dt.datetime,
            has_children: bool,
    ):
        self.block_id = block_id
        self.block_type = block_type
        self.created_time = created_time
        self.last_edited_time = last_edited_time
        self.has_children = has_children
        self.is_page_block = (self.block_type in PAGE_TYPES)
        self.is_supported_type = (self.block_type in SUPPORTED)
        self.can_have_children = (self.block_type in CAN_HAVE_CHILDREN)

        self.read_plain = ''
        self.read_rich = []

    def preview(self):
        message = {
            'block_id': self.block_id,
            'block_type': self.block_type,
            'has_children': self.has_children,
            'read_plain': self.read_plain
        }
        from pprint import pprint
        pprint(message)

    @classmethod
    def parse_retrieve(cls, response):
        self = cls(
            response['id'],
            response['type'],
            response['created_time'],
            response['last_edited_time'],
            response['has_children'],
        )
        self.parser_unit(response)
        return self

    @classmethod
    def parse_retrieve_frag(cls, response_frag):
        return cls.parse_retrieve(response_frag)

    @classmethod
    def parse_create_frag(cls, response_frag):
        return cls.parse_retrieve(response_frag)

    def parser_unit(self, rich_block_object):
        block_object = rich_block_object[self.block_type]

        if self.block_type in TEXT_TYPES:
            self.read_plain, self.read_rich = parse_rich_texts(block_object['text'])
        elif self.block_type in PAGE_TYPES:
            self.read_plain = block_object['title']
        elif self.block_type in UNSUPPORTED:
            self.read_plain = block_object
