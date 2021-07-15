from __future__ import annotations

from pprint import pprint

from notion_py.interface.read import Query
from notion_py.helpers import stopwatch
from ..constant_page_ids import ILGGI_ID
from .write_to_notion import ReadingPage, ReadingPageList
from .lib_gy import GoyangLibrary
from .lib_snu import scrap_snu_library


def update_reading_list():
    update_books(page_size=0)


def update_books(scrap_options=None, page_size=0):
    pagelist = get_pagelist(page_size=page_size)
    build_request_for_a_book = RequestBuilderforBook(scrap_options)
    for page in pagelist.values:
        try:
            build_request_for_a_book.execute(page)
            page.execute()
            stopwatch(f'-----{page.title}')
        except:
            pass
    stopwatch('서적류 완료')


def get_pagelist(page_size=0) -> ReadingPageList:
    query = Query(ILGGI_ID)
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['media_type'])
    ft = frame.equals_to_any('📖단행본', '☕연속간행물', '✒학습자료')
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['edit_status'])
    ft_overwrite_option = frame.equals_to_any(*ReadingPage.PROP_VALUE['edit_status_code'][1:3 + 1])
    ft_overwrite_option |= frame.is_empty()
    ft = ft & ft_overwrite_option
    # frame = query.filter_maker.by_text('📚제목')
    # ft &= frame.equals('어떻게 일할 것인가')
    query.push_filter(ft)
    pprint(query.apply())
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
        url = page.set_yes24_url_if_empty()
        if url:
            print(url)
            if 'yes24' in self.global_options:
                page.set_yes24_metadata(url)
            self.retrieve_lib_datas(page)
        page.set_edit_status()

    def set_contents_block(self, page: ReadingPage, contents):
        pass

    def retrieve_lib_datas(self, page: ReadingPage):
        datas = {}
        if 'gy_lib' in self.global_options:
            # noinspection PyTypeChecker
            res = self.gylib.execute(page.get_names())
            if res:
                datas.update(gy=res)
        if 'snu_lib' in self.global_options:
            res = scrap_snu_library(page.get_names())
            if res:
                datas.update(snu=res)
        page.set_lib_datas(datas)
