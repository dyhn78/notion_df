from abc import ABC, abstractmethod, ABCMeta

from .block_contents_encode import \
    ContentsEncoder, RichTextContentsEncoder, InlinePageContentsEncoder


class InlinePageContentsWriter(ABC):
    @abstractmethod
    def push_carrier(self, carrier: InlinePageContentsEncoder) \
            -> InlinePageContentsEncoder:
        pass

    def write_title(self, title: str) -> InlinePageContentsEncoder:
        writer = InlinePageContentsEncoder(title)
        return self.push_carrier(writer)

    """
    @abstractmethod
    def push_carrier(self, carrier: ContentsEncoder) \
            -> RichTextContentsEncoder:
        pass

    def write_title(self, title: str):
        writer = self.push_carrier(RichTextContentsEncoder('child_page'))
        writer.write_text(title)
        return writer
    """


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
    def write_paragraph(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_paragraph()
        writer.write_text(text_contents)
        return writer

    def write_heading_1(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_heading_1()
        writer.write_text(text_contents)
        return writer

    def write_heading_2(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_heading_2()
        writer.write_text(text_contents)
        return writer

    def write_heading_3(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_heading_3()
        writer.write_text(text_contents)
        return writer

    def write_bulleted_list(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_bulleted_list()
        writer.write_text(text_contents)
        return writer

    def write_numbered_list(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_numbered_list()
        writer.write_text(text_contents)
        return writer

    def write_to_do(self, text_contents: str, checked=False) -> RichTextContentsEncoder:
        writer = self.write_rich_to_do(checked=checked)
        writer.write_text(text_contents)
        return writer

    def write_toggle(self, text_contents: str) -> RichTextContentsEncoder:
        writer = self.write_rich_toggle()
        writer.write_text(text_contents)
        return writer
