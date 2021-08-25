from notion_py.interface.common import ValueCarrier
from ..property.unit import RichTextUnitWriter


class BlockWriter(ValueCarrier):
    # TODO : Children 을 가질 수 있게 수정하기.
    def __init__(self, block_type, value_type, contents=None):
        self._block_type = block_type
        self._value_type = value_type
        if contents is not None:
            self.contents = contents

    def unpack(self):
        res = {
            'object': 'block',
            'type': self._block_type,
        }
        res.update(**self.contents)
        return res

    def __wrap_to_block(self, value):
        return {self._value_type: value}

    @classmethod
    def page(cls, title):
        return cls('child_page', 'title', {'title': title})


class TextBlockWriter(BlockWriter, RichTextUnitWriter):
    value_type = 'text'

    def __init__(self, block_type, **kwargs):
        BlockWriter.__init__(self, block_type=block_type, value_type='text')
        RichTextUnitWriter.__init__(self, value_type='text', prop_name=block_type)
        self._kwargs = kwargs

    @property
    def contents(self):
        contents = RichTextUnitWriter.unpack(self)
        contents.update(**self._kwargs)
        return contents
