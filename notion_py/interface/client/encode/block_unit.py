from abc import abstractmethod

from notion_py.interface.struct import ValueCarrier
from notion_py.interface.client.encode.tabular_property_unit import RichTextUnitWriter


class BlockWriter(ValueCarrier):
    def __init__(self, block_type, block_name):
        self.block_type = block_type
        self.block_name = block_name

    def __bool__(self):
        return True

    @abstractmethod
    def _unwrap(self):
        pass

    def unpack(self):
        return dict(**self._unwrap(), type=self.block_name, object='block')


class PageBlockWriter(BlockWriter):
    def __init__(self, title):
        super().__init__(block_type='title', block_name='child_page')
        self.title = title

    def _unwrap(self):
        return {'title': self.title}


class RichTextBlockWriter(BlockWriter, RichTextUnitWriter):
    value_type = 'text'

    def __init__(self, block_name, **kwargs):
        BlockWriter.__init__(self, block_type='text', block_name=block_name)
        RichTextUnitWriter.__init__(self, prop_type='text', prop_name=block_name)
        self._kwargs = kwargs

    def _unwrap(self):
        contents = RichTextUnitWriter.unpack(self)
        contents.update(**self._kwargs)
        return contents
