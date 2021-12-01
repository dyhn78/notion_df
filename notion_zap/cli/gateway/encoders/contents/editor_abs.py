from abc import ABC, abstractmethod, ABCMeta

from .carrier import ContentsEncoder, RichTextContentsEncoder
from ..property.carrier import RichTextPropertyEncoder
from ..property.editor_abs import PropertyEncoder


class PageContentsWriter(ABC):
    @abstractmethod
    def push_encoder(self, carrier: PropertyEncoder):
        pass

    def write_rich_title(self) -> RichTextPropertyEncoder:
        writer = RichTextPropertyEncoder(prop_name='title', prop_type='title')
        return self.push_encoder(writer)

    def write_title(self, value: str):
        writer = self.write_rich_title()
        writer.write_text(value)
        return writer


class RichTextContentsWriter(ABC):
    @abstractmethod
    def push_encoder(self, carrier: ContentsEncoder) \
            -> RichTextContentsEncoder:
        pass

    def write_rich_paragraph(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('paragraph', True))

    def write_rich_heading_1(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('heading_1', False))

    def write_rich_heading_2(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('heading_2', False))

    def write_rich_heading_3(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('heading_3', False))

    def write_rich_bulleted_list(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('bulleted_list_item', True))

    def write_rich_numbered_list(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('numbered_list_item', True))

    def write_rich_to_do(self, checked=False) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('to_do', True, checked=checked))

    def write_rich_toggle(self) -> RichTextContentsEncoder:
        return self.push_encoder(RichTextContentsEncoder('toggle', True))


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


# class PageContentsWriterAsChild(ABC):
#     @abstractmethod
#     def push_carrier(self, carrier: ContentsEncoder) \
#             -> RichTextContentsEncoder:
#         pass
#
#     def write_rich_title(self) -> RichTextContentsEncoder:
#         return self.push_carrier(PageContentsEncoderAsChildBlock())
#
#     def write_title(self, value: str) -> RichTextContentsEncoder:
#         writer = self.write_rich_title()
#         writer.write_text(value)
#         return writer
