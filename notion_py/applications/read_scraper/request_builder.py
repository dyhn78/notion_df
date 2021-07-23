from __future__ import annotations

from notion_py.helpers import stopwatch
from .yes24 import scrap_yes24_url, scrap_yes24_metadata
from .reading_page import BookReadingPage, BookReadingPageList
from .lib_gy import GoyangLibrary
from .lib_snu import SNULibrary


def regular_scrap_in_ilggi(page_size=0):
    regular_scrap_for_books(page_size=page_size)


def regular_scrap_for_books(scrap_options=None, page_size=0):
    pagelist = BookReadingPageList.for_regular_scrap(page_size=page_size)
    request_builder = RequestBuilderforBook(scrap_options)
    for page in pagelist.values:
        stopwatch(f'{page.title}')
        request_builder.execute(page)
        page.execute()
    request_builder.quit()
    stopwatch('서적류 완료')


class RequestBuilderforBook:
    def __init__(self, global_scraper_options=None):
        if global_scraper_options is None:
            self.global_scraper_option = BookReadingPage.DEFAULT_SCRAPER_OPTION
        else:
            self.global_scraper_option = global_scraper_options
        if 'gy_lib' in self.global_scraper_option:
            self.gylib = GoyangLibrary()
        if 'snu_lib' in self.global_scraper_option:
            self.snulib = SNULibrary()

    def execute(self, page: BookReadingPage):
        url = page.get_yes24_url()
        if not url:
            url = scrap_yes24_url(page.get_names())
            page.set_yes24_url(url)
        if url:
            stopwatch(url)
            if ('yes24' in self.global_scraper_option and
                    'yes24' in page.local_scraper_option):
                metadata = scrap_yes24_metadata(url)
                page.set_yes24_metadata(metadata)
            lib_datas = self.scrap_lib_datas(page.get_names())
            page.set_lib_datas(lib_datas)
        page.set_edit_status()

    def scrap_lib_datas(self, book_names: tuple[str, str]):
        datas = {}
        if 'snu_lib' in self.global_scraper_option:
            # noinspection PyTypeChecker
            res = self.snulib.execute(book_names)
            if res:
                datas.update(snu=res)
        if 'gy_lib' in self.global_scraper_option:
            # noinspection PyTypeChecker
            res = self.gylib.execute(book_names)
            if res:
                datas.update(gy=res)
        return datas

    def quit(self):
        if 'gy_lib' in self.global_scraper_option:
            self.gylib.quit()


def reset_status_for_books(page_size=0):
    pagelist = BookReadingPageList.for_reset_library_info(page_size=page_size)
    for page in pagelist.values:
        page.props.set_overwrite(True)
        page.props.write.select(page.PROP_NAME['edit_status'], page.EDIT_STATUS['append'])
        page.props.write.checkbox(page.PROP_NAME['not_available'], False)
        page.execute()
    stopwatch('작업 완료')
