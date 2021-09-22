import re

from .yes24_url import scrap_yes24_url
from .yes24_metadata import scrap_yes24_metadata
from notion_py.interface import TypeName
from notion_py.interface.utility import stopwatch


class BookstoreScraper:
    # TODO : yes24에 자료 없을 경우 대비해 알라딘 등 추가 필요.
    def __init__(self, handler):
        self.handler = handler
        self.page: TypeName.tabular_page = handler.page
        self.props = self.page.props
        self.children = self.page.pagelist
        self.subpage_id = ''

    def execute(self):
        # pprint(self.props.read_full_of_all())
        url = self.get_url()
        if not url:
            url = scrap_yes24_url(self.handler.get_names())
            self.set_url(url)
        if url:
            if 'bookstore' in self.handler.targets:
                metadata = scrap_yes24_metadata(url)
                contents = self.set_metadata(metadata)
                self.set_contents_data(contents)
            stopwatch(f'bookstore: {url}')

    def get_url(self):
        url = self.props.read_at('url', default='')
        if 'bookstore' in url:
            return url
        else:
            return ''

    def set_url(self, url):
        if url:
            self.props.write_url_at('url', url)
        else:
            self.handler.status = self.handler.status_enum['url_missing']

    def set_metadata(self, metadata: dict):
        self.handler.set_overwrite_option(False)
        self.props.write_text_at('true_name', metadata['name'])
        self.props.write_text_at('subname', metadata['subname'])
        self.props.write_text_at('author', metadata['author'])
        self.props.write_text_at('publisher', metadata['publisher'])
        self.props.write_files_at('cover_image', 'cover_image')
        return metadata['contents']

    def set_contents_data(self, contents: list[str]):
        subpage = self.get_subpage()
        self.append_contents(subpage, contents)
        writer = self.props.write_rich_text_at('link_to_contents')
        writer.mention_page(subpage.master_id)

    def get_subpage(self) -> TypeName.inline_page:
        for block in self.children.pagelist:
            if isinstance(block, TypeName.inline_page) and \
                    self.page.title in block.contents.read():
                block.contents.write_title(f'={self.page.title}')
                break
        else:
            block = self.children.create_inline_page()
            block.contents.write_title(f'x={self.page.title}')
            block.execute()
        return block

    @staticmethod
    def append_contents(subpage: TypeName.inline_page, contents: list[str]):
        # TODO
        section = re.compile(r"\d+부[.:]? ")
        section_eng = re.compile(r"PART", re.IGNORECASE)

        chapter = re.compile(r"\d+장[.:]? ")
        chapter_eng = re.compile(r"CHAPTER", re.IGNORECASE)

        small_chapter = re.compile(r"\d+[.:] ")

        for text_line in contents:
            child = subpage.pagelist.create_text_block()
            contents = child.contents
            if re.findall(section, text_line) or re.findall(section_eng, text_line):
                contents.write_heading_2(text_line)
            elif re.findall(chapter, text_line) or re.findall(chapter_eng, text_line):
                contents.write_heading_3(text_line)
            elif re.findall(small_chapter, text_line):
                contents.write_paragraph(text_line)
            else:
                contents.write_toggle(text_line)
