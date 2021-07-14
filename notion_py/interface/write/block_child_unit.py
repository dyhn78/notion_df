from typing import Optional

from .property_unit import WriteRichTextProperty
from notion_py.interface.structure.carriers import ValueCarrier


class WriteBlock(ValueCarrier):
    def __init__(self, block_type, value_type, contents=None):
        self._block_type = block_type
        self._value_type = value_type
        if contents is not None:
            self.contents = contents

    def apply(self):
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


class WriteTextBlock(WriteBlock, WriteRichTextProperty):
    value_type = 'text'

    def __init__(self, block_type, plain_text_contents: Optional[str] = None, **kwargs):
        WriteBlock.__init__(self, block_type=block_type, value_type='text')
        WriteRichTextProperty.__init__(self, value_type='text', prop_name=block_type,
                                       plain_text_contents=plain_text_contents)
        self._kwargs = kwargs

    @property
    def contents(self):
        contents = WriteRichTextProperty.apply(self)
        contents.update(**self._kwargs)
        return contents
