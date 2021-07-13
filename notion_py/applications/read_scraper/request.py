from __future__ import annotations
import re

from notion_py.interface.write import PageListEditor, TabularPageEditor, AppendBlockChildren
from notion_py.interface.read import Query
from notion_py.interface.parse import BlockChildren
from ..constant_page_ids import ILGGI_ID
from .lib_gy import GoyangLibrary
from .lib_snu import scrap_snu_library
from .yes24 import get_yes24_url, scrap_yes24_metadata

MEDIA_TYPE = '🔵유형'
DOCX_NAME = '📚제목'
TRUE_NAME = '🔍원제(검색용)'
SUBNAME = '📚부제'
URL = '📚링크'
AUTHOR = '📚만든이'
PUBLISHER = '📚만든곳'
PAGE = '📚N(쪽+)'
COVER_IMAGE = '📚표지'
LINK_TO_CONTENTS = '📦이동'
LOCATION = '🔍위치'
EDIT_STATUS = '🔍준비'
EDIT_STATUS_CODE = [
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


def update_reading_list():
    update_books()


def update_books(scrap_options=None):
    pagelist = get_pagelist()
    build_request_for_a_book = RequestBuilderforBook(scrap_options)
    for page in pagelist.values:
        build_request_for_a_book.execute(page)
    pagelist.execute()


def get_pagelist() -> PageListEditor:
    query = Query(ILGGI_ID)
    frame = query.filter_maker.by_select(MEDIA_TYPE)
    ft_media_type = frame.equals_to_any(
        '☕가벼운 책', '🙇‍♂️무거운 책', '✒학습자료')
    frame = query.filter_maker.by_select(EDIT_STATUS)
    ft_overwrite_option = frame.equals_to_any(*EDIT_STATUS_CODE[1:3+1])
    ft = ft_media_type & ft_overwrite_option
    query.push_filter(ft)
    return ReadingPageListEditor.from_query(query)
    # return ReadingPageListEditor.from_query_and_retrieve_of_each_elements(query)


class RequestBuilderforBook:
    def __init__(self, gylib: GoyangLibrary, global_options=None):
        if global_options is None:
            self.global_options = ['yes24', 'gy_lib', 'snu_lib']
        else:
            self.global_options = global_options
        self.gylib = gylib

    def execute(self, page: ReadingPageEditor):
        page.set_local_edit_options()
        url = page.set_yes24_url()
        if url:
            if 'yes24' in self.global_options:
                page.set_yes24_metadata(url)
            self.set_lib_datas(page)
        else:
            page.scrap_status = EDIT_STATUS_CODE[6]
        page.set_edit_status()

    def set_contents_block(self, page: ReadingPageEditor, contents):
        pass

    def set_lib_datas(self, page: ReadingPageEditor):
        datas = {}
        if 'gy_lib' in self.global_options:
            datas.update(gy=self.gylib.execute(page.get_names()))
        if 'snu_lib' in self.global_options:
            datas.update(snu=scrap_snu_library(page.get_names()))

        datastrings = []
        added_gy_at_the_list = False
        if ('gy_lib' in self.global_options and
                datas['gy'][0] == self.gylib.str_gajwa_lib):
            datastrings.append(datas['gy'])
            added_gy_at_the_list = True
        if 'snu_lib' in self.global_options and datas['snu']:
            datastrings.append(datas['snu'])
        if (not added_gy_at_the_list and 'gy_lib' in self.global_options and
                datas['gy'][0] != self.gylib.str_failed):
            datastrings.append(datas['gy'])

        if datastrings:
            joined_string = '; '.join(datastrings)
            page.props.write.text(LOCATION, joined_string)
        else:
            page.scrap_status = EDIT_STATUS_CODE[7]


class ReadingPageEditor(TabularPageEditor):
    def __init__(self, parsed_page, parent_id):
        super().__init__(parsed_page, parent_id)
        self.edit_option = ''
        self.scrap_status = ''

    def set_local_edit_options(self: TabularPageEditor) -> None:
        edit_status = self.props.read[EDIT_STATUS]
        charref = re.compile(r'(?<=\().+(?=\))')
        self.edit_option = re.findall(charref, edit_status)[0]
        parser = {'append': (False, 'a'),
                  'continue': (False, 'r'),
                  'overwrite': (True, 'w')}
        self.props.overwrite, self.blocks.edit_mode = parser[self.edit_option]

    def get_names(self) -> tuple[str, str]:
        docx_name = self.props.read[DOCX_NAME]
        true_name = self.props.read[TRUE_NAME]
        return docx_name, true_name

    def set_yes24_url(self) -> str:
        if self.props.read_empty_value(URL):
            url = get_yes24_url(self.get_names())
            self.props.write.text(URL, url)
        else:
            url = self.props.read[URL]
        return url

    def set_yes24_metadata(self, url):
        res = scrap_yes24_metadata(url)
        self.props.write.text(TRUE_NAME, res['name'])
        self.props.write.text(SUBNAME, res['subname'])
        self.props.write.text(AUTHOR, res['author'])
        self.props.write.text(PUBLISHER, res['publisher'])
        self.props.write.number(PAGE, res['page'])
        self.props.write.files(COVER_IMAGE, res['cover_image'])
        self.set_contents_to_subpage(res['contents'])

    def set_contents_to_subpage(self, contents: list):
        # TODO : 비동기 프로그래밍으로 구현할 경우... 어떻게 해야 제일 효율적일지 모르겠다.
        subpage_id = self.get_or_create_subpage_id()
        link_to_contents = self.props.write_rich.text(LINK_TO_CONTENTS)
        link_to_contents.mention_page(self.page_id)

        subpage_patch = AppendBlockChildren(subpage_id)
        for text_line in contents:
            subpage_patch.children.write.toggle(text_line)
        subpage_patch.execute()

    def get_or_create_subpage_id(self):
        if self.blocks.read:
            block = self.blocks.read[0]
            if block.contents and self.title in block.contents:
                return block.block_id
        subpage_title = f'={self.title}'
        self.blocks.write.page(subpage_title)
        response = self.execute()[1]
        new_blocks = BlockChildren.from_response(response)
        return new_blocks.children[0].block_id

    def set_edit_status(self):
        if not self.scrap_status:
            if self.edit_option == 'append':
                self.scrap_status = EDIT_STATUS_CODE[4]
            elif self.edit_option == 'continue':
                self.scrap_status = EDIT_STATUS_CODE[4]
            elif self.edit_option == 'overwrite':
                self.scrap_status = EDIT_STATUS_CODE[8]
        self.props.write_rich.select(EDIT_STATUS, self.scrap_status)


class ReadingPageListEditor(PageListEditor):
    editor_unit = ReadingPageEditor
