import re
from pprint import pprint

from notion_py.applications.read_scraper.yes24 import get_yes24_url, scrap_yes24_metadata
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
        edit_status='🔍준비',
        not_available='🔍대출중'
    )
    PROP_VALUE = dict(
        edit_status_code=[
            '0️⃣⛳정보 없음',
            '1️⃣📥건너뛰기(continue)',
            '2️⃣📥백업 유지(append)',
            '3️⃣📥덮어쓰기(overwrite)',
            '4️⃣👤원제/표지 검정',
            '5️⃣👤차례/표지(docx/jpg) 복사',
            '6️⃣🔍링크 직접 찾기',
            '7️⃣🔍대출정보 직접 찾기',
            '8️⃣⛳스크랩 완료'
        ]
    )

    def __init__(self, parsed_page, parent_id):
        super().__init__(parsed_page, parent_id)
        self.edit_option = ''
        self.scrap_status = ''

    def set_local_edit_options(self) -> None:
        edit_status = self.props.read[self.PROP_NAME['edit_status']]
        charref = re.compile(r'(?<=\().+(?=\))')
        self.edit_option = re.findall(charref, edit_status)[0]
        parser = {'append': (False, 'a'),
                  'continue': (False, 'r'),
                  'overwrite': (True, 'w')}
        self.props._overwrite_parameter, self.children.edit_mode = parser[self.edit_option]

    def get_names(self) -> tuple[str, str]:
        docx_name = self.props.read[self.PROP_NAME['docx_name']][0]
        true_name = self.props.read[self.PROP_NAME['true_name']][0]
        return docx_name, true_name

    def set_yes24_url_if_empty(self) -> str:
        if self.props.read_empty_value(self.PROP_NAME['url']):
            url = get_yes24_url(self.get_names())
            self.props.write.url(self.PROP_NAME['url'], url)
        else:
            url = self.props.read[self.PROP_NAME['url']]
        return url

    def set_yes24_metadata(self, url):
        res = scrap_yes24_metadata(url)
        self.props.write.text(self.PROP_NAME['true_name'], res['name'])
        self.props.write.text(self.PROP_NAME['subname'], res['subname'])
        self.props.write.text(self.PROP_NAME['author'], res['author'])
        self.props.write.text(self.PROP_NAME['publisher'], res['publisher'])
        self.props.write.number(self.PROP_NAME['page'], res['page'])
        self.props.write.files(self.PROP_NAME['cover_image'], res['cover_image'])
        self.set_contents_to_subpage(res['contents'])

    def set_contents_to_subpage(self, contents: list):
        # TODO : 비동기 프로그래밍으로 구현할 경우... 어떻게 해야 제일 효율적일지 모르겠다.
        # TODO : mention_page 기능이 제대로 작동하지 않는 것 같다.
        subpage_id = self.get_or_create_subpage_id()
        link_to_contents = self.props.write_rich.text(self.PROP_NAME['link_to_contents'])
        link_to_contents.mention_page(subpage_id)

        subpage_patch = AppendBlockChildren(subpage_id)
        self.parse_contents_then_append(subpage_patch, contents)
        subpage_patch.execute()

    def get_or_create_subpage_id(self):
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
    def parse_contents_then_append(patch: AppendBlockChildren, contents: list):
        # TODO : (우선순위 높음) '장', '부' 따위를 heading으로 간주하는 기능 삽입.
        for text_line in contents:
            if text_line == '':
                continue
            patch.children.write.toggle(text_line)
        # pprint(subpage_patch.apply())

    def set_lib_datas(self, datas: dict):
        datastrings = []
        first_on_the_list = None
        if datas['gy'] and datas['gy']['lib_name'] == GoyangLibrary.str_gajwa_lib:
            first_on_the_list = 'gy'
        elif datas['snu']:
            first_on_the_list = 'snu'
        elif datas['gy'] and datas['gy']['lib_name'] != GoyangLibrary.str_failed:
            first_on_the_list = 'gy'
        else:
            self.scrap_status = self.PROP_VALUE['edit_status_code'][7]

        first_data = datas.pop(first_on_the_list)
        if first_on_the_list == 'gy':
            string, available = self.format_gy_lib(first_data)
        else:
            string, available = first_data, None
        datastrings.append(string)
        datastrings.extend(datas.values())

        joined_string = '; '.join(datastrings)
        self.props.write.text(self.PROP_NAME['location'], joined_string)
        if available is not None:
            self.props.write.checkbox(self.PROP_NAME['not_available'], not available)

    @staticmethod
    def format_gy_lib(res: dict):
        string = f"{res['lib_name']} {res['book_code']}"
        available = res['available']
        return string, available

    def set_edit_status(self):
        if not self.scrap_status:
            if self.edit_option == 'append':
                self.scrap_status = self.PROP_VALUE['edit_status_code'][4]
            elif self.edit_option == 'continue':
                self.scrap_status = self.PROP_VALUE['edit_status_code'][4]
            elif self.edit_option == 'overwrite':
                self.scrap_status = self.PROP_VALUE['edit_status_code'][8]
        self.props.set_overwrite(True)
        self.props.write.select(self.PROP_NAME['edit_status'], self.scrap_status)
        self.props.set_overwrite(False)


class ReadingPageList(PageList):
    unit_editor = ReadingPage
