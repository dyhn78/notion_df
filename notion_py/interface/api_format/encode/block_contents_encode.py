from abc import abstractmethod

from notion_py.interface.struct import ValueCarrier
from .property_encode import RichTextPropertyEncoder


class ContentsEncoder(ValueCarrier):
    def __init__(self, block_type, block_name):
        self.block_type = block_type
        self.block_name = block_name

    def __bool__(self):
        return True

    @abstractmethod
    def _unpack_contents(self):
        pass

    def unpack(self):
        return dict(**self._unpack_contents(), type=self.block_name, object='block')


class RichTextContentsEncoder(ContentsEncoder, RichTextPropertyEncoder):
    value_type = 'text'

    def __init__(self, block_name, **kwargs):
        ContentsEncoder.__init__(self, block_type='text', block_name=block_name)
        RichTextPropertyEncoder.__init__(self, prop_type='text', prop_name=block_name)
        self._kwargs = kwargs

    def _unpack_contents(self):
        contents = RichTextPropertyEncoder.unpack(self)
        contents.update(**self._kwargs)
        return contents


class InlinePageContentsEncoder(ContentsEncoder):
    def __init__(self, title):
        super().__init__(block_type='title', block_name='child_page')
        self.title = title

    def _unpack_contents(self):
        return {'title': self.title}
