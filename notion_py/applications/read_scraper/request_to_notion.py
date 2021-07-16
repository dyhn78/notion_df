from __future__ import annotations

from pprint import pprint

from notion_py.interface.read import Query
from notion_py.helpers import stopwatch
from .yes24 import scrap_yes24_url
from ..constant_page_ids import ILGGI_ID
from .write_to_notion import ReadingPage, ReadingPageList
from .lib_gy import GoyangLibrary
from .lib_snu import scrap_snu_library


def update_ilggi():
    update_books(page_size=0)


def update_books(scrap_options=None, page_size=0):
    pagelist = query_books(page_size=page_size)
    build_request_for_a_book = RequestBuilderforBook(scrap_options)
    for page in pagelist.values:
        stopwatch(f'{page.title}')
        build_request_for_a_book.execute(page)
        page.execute()
    stopwatch('서적류 완료')


class RequestBuilderforBook:
    def __init__(self, global_options=None):
        if global_options is None:
            self.global_options = ['yes24', 'gy_lib', 'snu_lib']
        else:
            self.global_options = global_options
        if 'gy_lib' in self.global_options:
            self.gylib = GoyangLibrary()

    def execute(self, page: ReadingPage):
        url = page.get_yes24_url()
        if not url:
            url = scrap_yes24_url(page.get_names())
            page.set_yes24_url(url)
        if url:
            stopwatch(url)
            if 'yes24' in self.global_options:
                page.set_yes24_metadata(url)
            lib_datas = self.scrap_lib_datas(page.get_names())
            page.set_lib_datas(lib_datas)
        page.set_edit_status()

    def scrap_lib_datas(self, book_names: tuple[str, str]):
        datas = {}
        if 'gy_lib' in self.global_options:
            # noinspection PyTypeChecker
            res = self.gylib.execute(book_names)
            if res:
                datas.update(gy=res)
        if 'snu_lib' in self.global_options:
            res = scrap_snu_library(book_names)
            if res:
                datas.update(snu=res)
        return datas


def query_books(page_size=0) -> ReadingPageList:
    query = Query(ILGGI_ID)
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['media_type'])
    ft = frame.equals_to_any('📖단행본', '☕연속간행물', '✒학습자료')
    frame = query.filter_maker.by_select(ReadingPage.PROP_NAME['edit_status'])
    ft_overwrite_option = frame.equals_to_any(*ReadingPage.STATUS_CODE[1:3 + 1])
    ft_overwrite_option |= frame.is_empty()
    ft_debug = frame.does_not_equal(ReadingPage.STATUS_CODE[4])
    ft = ft & ft_overwrite_option & ft_debug
    query.push_filter(ft)
    return ReadingPageList.from_query(query, page_size=page_size)
    # return ReadingPageList.from_query_and_retrieve_of_each_elements(query)
