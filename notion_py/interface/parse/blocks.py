from __future__ import annotations


class BlockChildren:
    def __init__(self, children: list[BlockChild]):
        self.children: list[BlockChild] = children

    @classmethod
    def from_response(cls, response):
        self = cls([])
        for rich_block_object in response['results']:
            self.children.append(BlockChild.from_response_frag(rich_block_object))
        return self


class BlockChild:
    def __init__(self, block_id: str, has_children: bool,
                 block_type: str, contents):
        self.block_id = block_id
        self.has_children = has_children
        self.block_type = block_type
        self.contents = contents

    @classmethod
    def from_response_frag(cls, rich_block_object):
        block_type = rich_block_object['type']
        block_object = rich_block_object[block_type]

        return cls(
            block_id=rich_block_object['id'],
            has_children=rich_block_object['has_children'],
            block_type=block_type,
            contents=cls._flatten(block_type, block_object)
        )

    @classmethod
    def _flatten(cls, block_type, block_object):

        if block_type in ["paragraph", "bulleted_list_item",
                          "numbered_list_item", "toggle", "to_do"]:
            return parse_rich_texts(block_object['text'])

        elif block_type == 'child_page':
            return block_object['title']

        elif block_type == 'unsupported':
            return block_object


def parse_rich_texts(rich_texts):
    plain_text = ''.join([rich_text_object['plain_text']
                          for rich_text_object in rich_texts])
    rich_text = []
    for rich_text_object in rich_texts:
        rich_text.append(
            {key: rich_text_object[key]
             for key in ['type', 'text', 'mention', 'equation']
             if key in rich_text_object}
        )
    return plain_text, rich_text
