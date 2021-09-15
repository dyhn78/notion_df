from __future__ import annotations

from notion_py.interface.utility import stopwatch
from .yes24 import scrap_yes24_url, scrap_yes24_metadata
from .reading_page import BookReadingPage
from .reading_dataframe import BookReadingQuerymaker
from .lib_gy import GoyangLibrary
from .lib_snu import SNULibrary


def scrap_readings(page_size=0):
    scrap_books(page_size=page_size)


def scrap_books(scrap_options=None, page_size=0):
    pagelist = BookReadingQuerymaker.query_regulars(page_size=page_size)
    request_builder = BookScraper(scrap_options)
    for page in pagelist:
        request_builder.execute(page)
    request_builder.quit()
    stopwatch('서적류 완료')


class BookScraper:
    def __init__(self, scraper_options=None):
        if scraper_options is None:
            self.global_scraper_option = BookReadingPage.DEFAULT_SCRAPER_OPTION
        else:
            self.global_scraper_option = scraper_options
        if 'gy_lib' in self.global_scraper_option:
            self.gylib = GoyangLibrary()
        if 'snu_lib' in self.global_scraper_option:
            self.snulib = SNULibrary()

    def quit(self):
        if 'gy_lib' in self.global_scraper_option:
            self.gylib.quit()
        if 'snu_lib' in self.global_scraper_option:
            self.snulib.quit()

    def execute(self, page: BookReadingPage):
        print(f'____{page.title}____')
        url = page.get_yes24_url()
        if not url:
            url = scrap_yes24_url(page.get_names())
            page.set_yes24_url(url)

        if url:
            stopwatch(url)
            if 'bookstore' in page.targets:
                metadata = scrap_yes24_metadata(url)
                page.set_yes24_metadata(metadata)

        lib_datas = {}
        book_names = page.get_names()
        if any(lib in page.targets
               for lib in ['snu_lib', 'gy_lib']):
            if 'snu_lib' in page.targets:
                # noinspection PyTypeChecker
                snu_lib = self.snulib.execute(book_names)
                if snu_lib:
                    stopwatch(snu_lib)
                    lib_datas.update(snu=snu_lib)
            if 'gy_lib' in page.targets:
                # noinspection PyTypeChecker
                gy_lib = self.gylib.execute(book_names)
                if gy_lib:
                    stopwatch(gy_lib['lib_name'])
                    lib_datas.update(gy=gy_lib)
            page.set_lib_datas(lib_datas)

        page.set_edit_status()
        page.execute()
