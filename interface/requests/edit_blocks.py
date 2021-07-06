from interface.requests.edit_property_unit import RichTextProperty
from interface.requests.structures import ValueCarrier


class Block(ValueCarrier):
    _block_type = 'None'
    _content_type = 'None'

    def __init__(self, block_content):
        super().__init__()
        self.block_content = block_content

    def apply(self):
        return {
            'object': 'block',
            'type': self._block_type,
            self._block_type: self.block_content
        }

    def __wrap_to_block(self, value):
        return {self._content_type: value}


class TitleBlock(Block):
    _block_type = 'child_page'
    _content_type = 'title'

    def __init__(self, title):
        super().__init__(self.__wrap_to_block(title))


class TextBlock(Block, RichTextProperty):
    _content_type = 'text'

    def __init__(self, block_type):
        self._block_type = block_type
        RichTextProperty.__init__(self, prop_name='text', value_type='text')

    def apply(self):
        self.block_content = RichTextProperty.apply(self)
        return Block.apply(self)


class PlainTextBlock(TextBlock):
    def __init__(self, text_content, block_type):
        super().__init__(block_type)
        self.append_text(text_content)


class TodoBlock(TextBlock):
    _block_type = 'to_do'

    def __init__(self, checked=True):
        super().__init__(self._block_type)
        self.checked = checked

    def apply(self):
        self.block_content = RichTextProperty.apply(self)
        self.block_content.update(checked=self.checked)
        return Block.apply(self)


class PlainTodoBlock(TodoBlock):
    def __init__(self, text_content, checked=True):
        super().__init__(checked)
        self.append_text(text_content)
