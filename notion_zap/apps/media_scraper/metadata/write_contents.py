import re

from notion_zap.cli.editors import PageItem, Root


class ContentsWriter:
    def __call__(self, page: PageItem, contents: list[str]):
        if not contents:
            return
        max_depth = max(self.get_depth(text_line) for text_line in contents)
        for text_line in contents:
            block = page.items.open_new_text()
            depth = self.get_depth(text_line)
            if depth != 0:
                depth += (4 - max_depth)
            self.write_a_line(block, text_line, depth)

    @staticmethod
    def write_a_line(block, text_line, depth):
        if depth == 1:
            block.write_heading_1(text_line)
        elif depth == 2:
            block.write_heading_2(text_line)
        elif depth == 3:
            block.write_heading_3(text_line)
        elif depth == 4:
            block.write_paragraph(text_line)
        else:
            block.write_toggle(text_line)

    def get_depth(self, text_line: str):
        if self.VOLUME_KOR.findall(text_line) or self.VOLUME_ENG.findall(text_line):
            return 1
        if self.SECTION_KOR.findall(text_line) or self.SECTION_ENG.findall(text_line):
            return 2
        elif self.CHAPTER_KOR.findall(text_line) or self.CHAPTER_ENG.findall(text_line):
            return 3
        elif self.PASSAGE.findall(text_line):
            return 4
        else:
            return 0

    VOLUME_KOR = re.compile(r"\d+권[.:]? ")
    VOLUME_ENG = re.compile(r"VOLUME", re.IGNORECASE)

    SECTION_KOR = re.compile(r"\d+부[.:]? ")
    SECTION_ENG = re.compile(r"PART", re.IGNORECASE)

    CHAPTER_KOR = re.compile(r"\d+장[.:]? ")
    CHAPTER_ENG = re.compile(r"CHAPTER", re.IGNORECASE)

    PASSAGE = re.compile(r"\d+[.:] ")


if __name__ == '__main__':
    writer = ContentsWriter()
    root = Root()
    page1 = root.space.text_item('')
    contents1 = ['1', '2', '3']
    writer(page1, contents1)
    root.space.save_preview()
