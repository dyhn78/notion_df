from __future__ import annotations

from .rich_text import parse_rich_texts
from ..struct.root import Printable

PAGE_TYPES = {"child_page"}
CAN_HAVE_CHILDREN = {"paragraph", "bulleted_list_item",
                     "numbered_list_item", "toggle", "to_do"}
TEXT_TYPES = CAN_HAVE_CHILDREN | {"heading_1", "heading_2", "heading_3"}
SUPPORTED = TEXT_TYPES | PAGE_TYPES
UNSUPPORTED = {"unsupported"}


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
    def __init__(self, block_id: str, block_type: str):
        self.block_id = block_id
        self.block_type = block_type
        self.has_children = False
        self.is_page_block = (self.block_type in PAGE_TYPES)
        self.is_supported_type = (self.block_type in SUPPORTED)
        self.can_have_children = (self.block_type in CAN_HAVE_CHILDREN)

        self.read_plain = ''
        self.read_rich = []

    def pprint(self):
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
        self = cls(block_id=response['id'],
                   block_type=response['type'])
        self.has_children = response['has_children']
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
