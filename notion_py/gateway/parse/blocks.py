from __future__ import annotations

from .rich_text import parse_rich_texts

CAN_HAVE_CHILDREN = {"paragraph", "bulleted_list_item",
                     "numbered_list_item", "toggle", "to_do"}
TEXT_TYPES = CAN_HAVE_CHILDREN | {"heading_1", "heading_2", "heading_3"}
PAGE_TYPES = {"child_page"}
SUPPORTED = TEXT_TYPES | PAGE_TYPES
UNSUPPORTED = {"unsupported"}


class BlockChildrenParser:
    def __init__(self, response: dict):
        self.values: list[BlockChildParser] = \
            [BlockChildParser.fetch_response_frag(rich_block_object)
             for rich_block_object in response['results']]
        self.read_plain: list[str] = [child.read_plain for child in self.values]
        self.read_rich: list[list] = [child.read_rich for child in self.values]


class BlockChildParser:
    def __init__(self, block_id: str, block_type: str, has_children: bool):
        self.block_id = block_id
        self.block_type = block_type
        self.has_children = has_children
        self.is_supported_type = (self.block_type in SUPPORTED)
        self.can_have_children = (self.block_type in CAN_HAVE_CHILDREN)

        self.read_plain = ''
        self.read_rich = []

    @classmethod
    def fetch_response_frag(cls, rich_block_object):
        self = cls(
            block_id=rich_block_object['id'],
            block_type=rich_block_object['type'],
            has_children=rich_block_object['has_children']
        )
        self.parse_unit(rich_block_object)
        return self

    def parse_unit(self, rich_block_object):
        block_object = rich_block_object[self.block_type]

        if self.block_type in TEXT_TYPES:
            self.read_plain, self.read_rich = parse_rich_texts(block_object['text'])
        elif self.block_type in PAGE_TYPES:
            self.read_plain = block_object['title']
        elif self.block_type in UNSUPPORTED:
            self.read_plain = block_object
