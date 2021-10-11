from abc import abstractmethod

from notion_py.interface.encoder.rich_text import RichTextObjectEncoder
from notion_py.interface.common.struct import ValueCarrier


class ContentsEncoder(ValueCarrier):
    def __init__(self, value_type, block_name):
        self.value_type = value_type
        self.block_name = block_name

    def __bool__(self):
        return True

    @abstractmethod
    def _contents_value(self):
        pass

    def unpack(self):
        return dict(**self._contents_value(),
                    object='block',
                    type=self.block_name)


class RichTextContentsEncoder(ContentsEncoder, RichTextObjectEncoder):
    prop_type = 'text'

    def __init__(self, block_name, **kwargs):
        ContentsEncoder.__init__(self, value_type='text', block_name=block_name)
        RichTextObjectEncoder.__init__(self)
        self._kwargs = kwargs

    def _contents_value(self):
        contents = {
            self.block_name: {self.value_type: RichTextObjectEncoder.unpack(self),
                              **self._kwargs},
            # dict(type = self.block_name)  -- prior to 2021-08-16
        }
        return contents


class PageContentsEncoderAsChildBlock(ContentsEncoder, RichTextObjectEncoder):
    def __init__(self):
        ContentsEncoder.__init__(self, value_type='text', block_name='child_page')
        RichTextObjectEncoder.__init__(self)

    def _contents_value(self):
        contents = {
            'child_page': {self.value_type: RichTextObjectEncoder.unpack(self)},
            # dict(type = 'child_page')  -- prior to 2021-08-16
        }
        return contents


"""
class PageContentsEncoderAsChildBlock(ContentsEncoder):
    def __init__(self, title):
        super().__init__(value_type='title', block_name='child_page')
        self.title = title

    def _contents_value(self):
        return {'child_page': {'title': self.title}}
"""