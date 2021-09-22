from abc import ABC, abstractmethod, ABCMeta

from .maker import ContentsEncoder, RichTextContentsEncoder
from ..property.maker import RichTextPropertyEncoder
from ..property.wrapper import PropertyEncoder


class PageContentsWriterAsChildBlock(ABC):
    @abstractmethod
    def push_carrier(self, carrier: ContentsEncoder) \
            -> RichTextContentsEncoder:
        pass

    def write_rich_title(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('title'))

    def write_title(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_title()
        writer.write_text(value)
        return writer


class PageContentsWriterAsIndepPage(ABC):
    @abstractmethod
    def push_carrier(self, carrier: PropertyEncoder):
        pass

    def write_rich_title(self) -> RichTextPropertyEncoder:
        writer = RichTextPropertyEncoder(prop_type='title', prop_name='title')
        return self.push_carrier(writer)

    def write_title(self, value: str):
        writer = self.write_rich_title()
        writer.write_text(value)
        return writer


"""class PageContentsWriterAsChildBlock(ABC):
    @abstractmethod
    def push_carrier(self, carrier: PageContentsEncoderAsChildBlock) \
            -> PageContentsEncoderAsChildBlock:
        pass

    def write_title(self, title: str) -> PageContentsEncoderAsChildBlock:
        writer = PageContentsEncoderAsChildBlock(title)
        return self.push_carrier(writer)"""


class RichTextContentsWriter(ABC):
    @abstractmethod
    def push_carrier(self, carrier: ContentsEncoder) \
            -> RichTextContentsEncoder:
        pass

    def write_rich_paragraph(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('paragraph'))

    def write_rich_heading_1(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('heading_1'))

    def write_rich_heading_2(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('heading_2'))

    def write_rich_heading_3(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('heading_3'))

    def write_rich_bulleted_list(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('bulleted_list_item'))

    def write_rich_numbered_list(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('numbered_list_item'))

    def write_rich_to_do(self, checked=False) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('to_do', checked=checked))

    def write_rich_toggle(self) -> RichTextContentsEncoder:
        return self.push_carrier(RichTextContentsEncoder('toggle'))


class TextContentsWriter(RichTextContentsWriter, metaclass=ABCMeta):
    def write_paragraph(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_paragraph()
        writer.write_text(value)
        return writer

    def write_heading_1(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_heading_1()
        writer.write_text(value)
        return writer

    def write_heading_2(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_heading_2()
        writer.write_text(value)
        return writer

    def write_heading_3(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_heading_3()
        writer.write_text(value)
        return writer

    def write_bulleted_list(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_bulleted_list()
        writer.write_text(value)
        return writer

    def write_numbered_list(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_numbered_list()
        writer.write_text(value)
        return writer

    def write_to_do(self, value: str, checked=False) -> RichTextContentsEncoder:
        writer = self.write_rich_to_do(checked=checked)
        writer.write_text(value)
        return writer

    def write_toggle(self, value: str) -> RichTextContentsEncoder:
        writer = self.write_rich_toggle()
        writer.write_text(value)
        return writer
