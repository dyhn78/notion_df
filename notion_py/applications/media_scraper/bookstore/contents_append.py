import re

from notion_py.interface import TypeName


class AppendContents:
    def __init__(self, subpage: TypeName.inline_page, contents: list[str]):
        self.page = subpage
        self.contents = contents

    def execute(self):
        max_depth = 0
        for text_line in self.contents:
            depth = self.get_depth(text_line)
            if depth != 0:
                max_depth = max(max_depth, depth)
        for text_line in self.contents:
            block = self.page.sphere.create_text_block()
            depth = self.get_depth(text_line)
            if depth != 0:
                depth += (4 - max_depth)
            self.write_unit(block, text_line, depth)

    def get_depth(self, text_line):
        if self.volume.findall(text_line) or self.volume_eng.findall(text_line):
            return 1
        if self.section.findall(text_line) or self.section_eng.findall(text_line):
            return 2
        elif self.chapter.findall(text_line) or self.chapter_eng.findall(text_line):
            return 3
        elif self.small_chapter.findall(text_line):
            return 4
        else:
            return 0

    @staticmethod
    def write_unit(block, text_line, depth):
        if depth == 1:
            block.contents.write_heading_1(text_line)
        elif depth == 2:
            block.contents.write_heading_2(text_line)
        elif depth == 3:
            block.contents.write_heading_3(text_line)
        elif depth == 4:
            block.contents.write_paragraph(text_line)
        else:
            block.contents.write_toggle(text_line)

    volume = re.compile(r"\d+권[.:]? ")
    volume_eng = re.compile(r"VOLUME", re.IGNORECASE)

    section = re.compile(r"\d+부[.:]? ")
    section_eng = re.compile(r"PART", re.IGNORECASE)

    chapter = re.compile(r"\d+장[.:]? ")
    chapter_eng = re.compile(r"CHAPTER", re.IGNORECASE)

    small_chapter = re.compile(r"\d+[.:] ")
