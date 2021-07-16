import re

from notion_py.interface.editor import TabularPage, PageList
from notion_py.interface.parse import PageParser
from notion_py.interface.write import AppendBlockChildren, CreateBasicPage
from .lib_gy import GoyangLibrary


class ReadingPage(TabularPage):
    PROP_NAME = dict(
        media_type='🔵유형',
        docx_name='📚제목',
        true_name='🔍원제(검색용)',
        subname='📚부제',
        url='📚링크',
        author='📚만든이',
        publisher='📚만든곳',
        page='📚N(쪽+)',
        cover_image='📚표지',
        link_to_contents='📦이동',
        location='🔍위치',
        edit_status='🏁준비',
        not_available='🔍대출중'
    )
    MEDIA_TYPES = ['📖단행본', '☕연속간행물', '✒학습자료']
    EDIT_STATUS = {
        'pass': '0️⃣⛳정보 없음',
        'append': '1️⃣📥백업 유지(append)',
        'overwrite': '2️⃣📥덮어쓰기(overwrite)',
        'continue': '3️⃣📥건너뛰기(continue)',
        'done': '4️⃣👤원제/표지 검정',
        'url_missing': '5️⃣🔍링크 직접 찾기',
        'lib_missing': '6️⃣🔍대출정보 직접 찾기',
        'edit_strongly_done': '7️⃣⛳스크랩 완료'
    }

    def __init__(self, parsed_page, parent_id):
        super().__init__(parsed_page, parent_id)
        self.edit_option = ''
        self.scrap_status = ''

    def get_edit_options(self) -> None:
        edit_status = self.props.read[self.PROP_NAME['edit_status']]
        if not edit_status:
            self.edit_option = 'append'
        else:
            charref = re.compile(r'(?<=\().+(?=\))')
            self.edit_option = re.findall(charref, edit_status)[0]
        parser = {'append': (False, 'a'),
                  'continue': (False, 'r'),
                  'overwrite': (True, 'w')}
        props_option, children_option = parser[self.edit_option]
        self.props.set_overwrite(props_option)
        self.children.set_overwrite(children_option)

    def set_edit_status(self):
        self.get_edit_options()
        if not self.scrap_status:
            if self.edit_option == 'append':
                self.scrap_status = self.EDIT_STATUS['done']
            elif self.edit_option == 'continue':
                self.scrap_status = self.EDIT_STATUS['done']
            elif self.edit_option == 'overwrite':
                self.scrap_status = self.EDIT_STATUS['edit_strongly_done']
        self.props.set_overwrite(True)
        self.props.write.select(self.PROP_NAME['edit_status'], self.scrap_status)
        self.props.set_overwrite(False)

    def get_names(self) -> tuple[str, str]:
        docx_name = self.props.read[self.PROP_NAME['docx_name']][0]
        true_name = self.props.read[self.PROP_NAME['true_name']][0]
        return docx_name, true_name

    def get_yes24_url(self):
        url = self.props.read[self.PROP_NAME['url']]
        if 'yes24' in url:
            return url
        return ''

    def set_yes24_url(self, url: str):
        if url:
            self.props.write.url(self.PROP_NAME['url'], url)
        else:
            self.scrap_status = self.EDIT_STATUS['url_missing']

    def set_yes24_metadata(self, metadata: dict):
        self.get_edit_options()
        self.props.write.text(self.PROP_NAME['true_name'], metadata['name'])
        self.props.write.text(self.PROP_NAME['subname'], metadata['subname'])
        self.props.write.text(self.PROP_NAME['author'], metadata['author'])
        self.props.write.text(self.PROP_NAME['publisher'], metadata['publisher'])
        self.props.write.number(self.PROP_NAME['page'], metadata['page'])
        self.props.write.files(self.PROP_NAME['cover_image'], metadata['cover_image'])
        self.set_contents_to_subpage(metadata['contents'])

    def set_contents_to_subpage(self, contents: list):
        # TODO : 비동기 프로그래밍으로 구현할 경우... 어떻게 해야 제일 효율적일지 모르겠다.
        subpage_id = self.get_or_make_subpage_id()
        self.props.set_overwrite(True)
        link_to_contents = self.props.write_rich.text(self.PROP_NAME['link_to_contents'])
        link_to_contents.mention_page(subpage_id)

        subpage_patch = AppendBlockChildren(subpage_id)
        self.parse_contents_then_append(subpage_patch, contents)
        subpage_patch.execute()

    def get_or_make_subpage_id(self):
        # TODO : GenerativeRequestor 구현되면 아래 구문을 삽입한다.
        """
        if self.children.read:
            block = self.children.read[0]
            if block.contents and self.title in block.contents:
                return block.block_id
        """
        subpage_patch = CreateBasicPage(self.page_id)
        subpage_patch.props.write.title(f'={self.title}')
        response = subpage_patch.execute()
        return PageParser.from_retrieve_response(response).page_id

    @staticmethod
    def parse_contents_then_append(patch: AppendBlockChildren, contents: list[str]):
        section = re.compile(r"\d+부[.:]? ")
        section_eng = re.compile(r"PART", re.IGNORECASE)

        chapter = re.compile(r"\d+장[.:]? ")
        chapter_eng = re.compile(r"CHAPTER", re.IGNORECASE)

        small_chapter = re.compile(r"\d+[.:] ")

        for text_line in contents:
            if re.findall(section, text_line) or re.findall(section_eng, text_line):
                patch.children.write.heading_2(text_line)
            elif re.findall(chapter, text_line) or re.findall(chapter_eng, text_line):
                patch.children.write.heading_3(text_line)
            elif re.findall(small_chapter, text_line):
                patch.children.write.paragraph(text_line)
            else:
                patch.children.write.toggle(text_line)

    def set_lib_datas(self, datas: dict):
        datastrings = []
        if 'gy' in datas.keys() and \
                datas['gy']['lib_name'] == GoyangLibrary.str_gajwa_lib:
            first_on_the_list = 'gy'
        elif 'snu' in datas.keys():
            first_on_the_list = 'snu'
        elif 'gy' in datas.keys():
            first_on_the_list = 'gy'
        else:
            self.scrap_status = self.EDIT_STATUS['lib_missing']
            return

        first_data = datas.pop(first_on_the_list)
        if first_on_the_list == 'gy':
            string, available = self.format_gy_lib(first_data)
        else:
            string, available = first_data, None
        datastrings.append(string)
        datastrings.extend(datas.values())
        joined_string = '; '.join(datastrings)

        self.props.set_overwrite(True)
        self.props.write.text(self.PROP_NAME['location'], joined_string)
        if available is not None:
            self.props.write.checkbox(self.PROP_NAME['not_available'], not available)

    @staticmethod
    def format_gy_lib(res: dict):
        string = f"{res['lib_name']}"
        if book_code := res['book_code']:
            string += f" {book_code}"
        available = res['available']
        return string, available


class ReadingPageList(PageList):
    def __init__(self, parsed_query, parent_id):
        super().__init__(parsed_query, parent_id)
        self.values = [ReadingPage(parsed_page, parent_id)
                       for parsed_page in parsed_query.values]
