from abc import ABC, abstractmethod, ABCMeta
from typing import Union

from .block_unit import BlockWriter, RichTextBlockWriter, PageBlockWriter


class RichBlockContents(ABC):
    @abstractmethod
    def _push(self, carrier: BlockWriter) \
            -> Union[RichTextBlockWriter, PageBlockWriter]:
        pass

    def write_rich_paragraph(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('paragraph'))

    def write_rich_heading_1(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('heading_1'))

    def write_rich_heading_2(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('heading_2'))

    def write_rich_heading_3(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('heading_3'))

    def write_rich_bulleted_list(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('bulleted_list_item'))

    def write_rich_numbered_list(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('numbered_list_item'))

    def write_rich_to_do(self, checked=False) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('to_do', checked=checked))

    def write_rich_toggle(self) -> RichTextBlockWriter:
        return self._push(RichTextBlockWriter('toggle'))


class BlockContents(RichBlockContents, metaclass=ABCMeta):
    def write_page_block(self, title: str) -> PageBlockWriter:
        writer = PageBlockWriter(title)
        return self._push(writer)

    def write_paragraph(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_paragraph()
        writer.write_text(text_contents)
        return self._push(writer)

    def write_heading_1(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_heading_1()
        writer.write_text(text_contents)
        return self._push(writer)

    def write_heading_2(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_heading_2()
        writer.write_text(text_contents)
        return self._push(writer)

    def write_heading_3(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_heading_3()
        writer.write_text(text_contents)
        return self._push(writer)

    def write_bulleted_list(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_bulleted_list()
        writer.write_text(text_contents)
        return self._push(writer)

    def write_numbered_list(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_numbered_list()
        writer.write_text(text_contents)
        return self._push(writer)

    def write_to_do(self, text_contents: str, checked=False) -> RichTextBlockWriter:
        writer = self.write_rich_to_do(checked=checked)
        writer.write_text(text_contents)
        return self._push(writer)

    def write_toggle(self, text_contents: str) -> RichTextBlockWriter:
        writer = self.write_rich_toggle()
        writer.write_text(text_contents)
        return self._push(writer)
