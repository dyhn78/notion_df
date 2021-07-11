from .edit_property_unit import RichTextProperty
from ..structure.carriers import ValueCarrier


class Block(ValueCarrier):
    def __init__(self, block_type, value_type, contents):
        self._block_type = block_type
        self._value_type = value_type
        if contents is not None:
            self.contents = contents

    def apply(self):
        return {
            'object': 'block',
            'type': self._block_type,
            self._block_type: self.contents
        }

    def __wrap_to_block(self, value):
        return {self._value_type: value}

    @classmethod
    def page(cls, title):
        wrapped_title = {'title': title}
        return cls('child_page', wrapped_title, None)


class PageBlock(Block):
    def __init__(self, title):
        wrapped_title = {'title': title}
        super().__init__('child_page', wrapped_title, None)


class TextBlock(Block, RichTextProperty):
    _value_type = 'text'

    def __init__(self, block_type, **kwargs):
        Block.__init__(self, block_type, 'text', None)
        RichTextProperty.__init__(self, 'text', 'text')
        self._kwargs = kwargs

    @classmethod
    def plain_form(cls, text_content, block_type, **kwargs):
        self = cls(block_type, **kwargs)
        self.write_text(text_content)
        return self

    @property
    def contents(self):
        contents = RichTextProperty.apply(self)
        contents.update(**self._kwargs)
        return contents
