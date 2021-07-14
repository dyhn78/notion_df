from __future__ import annotations

from collections import defaultdict

from notion_py.interface.read import Query
from ..constant_page_ids import ILGGI_ID
from .db_attributes import ReadingPage, ReadingPageList
from .lib_gy import GoyangLibrary
from .lib_snu import scrap_snu_library


def update_reading_list():
    update_books(page_size=1)


def update_books(scrap_options=None, page_size=0):
    pagelist = get_pagelist(page_size=page_size)
    build_request_for_a_book = RequestBuilderforBook(scrap_options)
    for page in pagelist.values:
        build_request_for_a_book.execute(page)
    pagelist.execute()


def get_pagelist(page_size=0) -> ReadingPageList:
    query = Query(ILGGI_ID)
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['media_type'])
    ft_media_type = frame.equals_to_any(
        '☕가벼운 책', '🙇‍♂️무거운 책', '✒학습자료')
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['edit_status'])
    ft_overwrite_option = frame.equals_to_any(*ReadingPage.PROP_VALUE['edit_status_code'][1:3 + 1])
    ft = ft_media_type & ft_overwrite_option
    query.push_filter(ft)
    return ReadingPageList.from_query(query, page_size=page_size)
    # return ReadingPageList.from_query_and_retrieve_of_each_elements(query)


class RequestBuilderforBook:
    def __init__(self, global_options=None):
        if global_options is None:
            self.global_options = ['yes24', 'gy_lib', 'snu_lib']
        else:
            self.global_options = global_options
        if 'gy_lib' in self.global_options:
            self.gylib = GoyangLibrary()

    def execute(self, page: ReadingPage):
        page.set_local_edit_options()
        url = page.set_yes24_url_if_empty()
        if url:
            if 'yes24' in self.global_options:
                page.set_yes24_metadata(url)
            self.retrieve_lib_datas(page)
        else:
            page.scrap_status = page.PROP_VALUE['edit_status_code'][6]
        page.set_edit_status()

    def set_contents_block(self, page: ReadingPage, contents):
        pass

    def retrieve_lib_datas(self, page: ReadingPage):
        datas = defaultdict(None)
        if 'gy_lib' in self.global_options:
            datas.update(gy=self.gylib.execute(page.get_names()))
        if 'snu_lib' in self.global_options:
            datas.update(snu=scrap_snu_library(page.get_names()))
        page.set_lib_datas(datas)
