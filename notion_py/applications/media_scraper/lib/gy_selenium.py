from __future__ import annotations
from typing import Optional
from selenium.common.exceptions import StaleElementReferenceException, \
    NoSuchElementException

from notion_py.applications.media_scraper.common.selenium import SeleniumScraper
from notion_py.applications.media_scraper.common.helpers import try_method_twice, remove_emoji


class GoyangLibrary(SeleniumScraper):
    DRIVER_CNT = 2
    GAJWA_LIB = '가좌도서관'
    OTHER_LIB = '고양시 상호대차'

    def __init__(self):
        super().__init__()
        self.DRIV_AVAIL = self.drivers[0]
        self.DRIV_CODE = self.drivers[1]
        self.available_somewhere = False
        self.best_option = {}

    @try_method_twice
    def execute(self, book_name: str) -> Optional[dict]:
        """
        :return: [도서관 이름: str('가좌도서관', '고양시 상호대차', '스크랩 실패'),
                    현재 대출 가능: bool,
                    서지번호: str('가좌도서관'일 경우에만 non-empty)]
        """
        self.reset_instance()
        self.load_search_results(book_name)
        self.review_search_results()
        return self.best_option

    def reset_instance(self):
        self.available_somewhere = False
        self.best_option = {}

    def load_search_results(self, book_name):
        self.load_main_page()
        self.DRIV_AVAIL.implicitly_wait(3)
        self.insert_book_name(book_name)
        self.click_search_button()
        self.DRIV_AVAIL.implicitly_wait(3)

    def load_main_page(self):
        url_main_page = 'https://www.goyanglib.or.kr/center/data/search.asp'
        self.DRIV_AVAIL.get(url_main_page)

    def insert_book_name(self, book_name):
        tag_input_box = '#a_q'
        input_box = self.DRIV_AVAIL.find_element_by_css_selector(tag_input_box)
        book_name = remove_emoji(book_name)
        input_box.send_keys(book_name)

    def click_search_button(self):
        tag_search_button = '#sb1 > a'
        search_button = self.DRIV_AVAIL.find_element_by_css_selector(tag_search_button)
        search_button.click()

    def review_search_results(self):
        page_buttons = self.get_page_buttons()
        for bb, button in enumerate(page_buttons):
            try:
                if bb != 0:
                    button.click()
                    self.DRIV_AVAIL.implicitly_wait(5)
            except StaleElementReferenceException:
                return
            if not (lib_names := self.get_lib_names()):
                return
            for i, lib_name in enumerate(lib_names):
                needs_detail_info = '가좌' in lib_name
                available_here = self.get_availability(i)
                if needs_detail_info:
                    self.load_detail_info(i)
                    self.DRIV_CODE.implicitly_wait(3)
                    book_code = self.get_book_code()
                    self.update_best_option(self.GAJWA_LIB, available_here, book_code)
                    return
                elif available_here and not self.available_somewhere:
                    self.available_somewhere = True
                    self.update_best_option(self.OTHER_LIB, True, '')

    def get_page_buttons(self):
        tag_no_book = '#lists > ul > li'
        no_book = self.DRIV_AVAIL.find_elements_by_css_selector(tag_no_book)
        if no_book and '검색하신 도서가 없습니다' in no_book[0].text:
            return []
        tag_page_buttons = '#pagelist > ul > li > a'
        page_buttons = self.DRIV_AVAIL.find_elements_by_css_selector(tag_page_buttons)
        page_buttons = page_buttons[1:-1]
        return page_buttons

    def get_lib_names(self):
        tag_lib_name = '#lists > ul > li > dl > dd:nth-child(3)'
        elms_lib_name = self.DRIV_AVAIL.find_elements_by_css_selector(tag_lib_name)
        return [lib_name.text for lib_name in elms_lib_name]

    def get_availability(self, i):
        """
        self.driv_main.find_element_by_css_selector(tag_availability).text
        = '대출(가능), 예약(불가능) \n ..'
        여기서 split(',')[0] 하면 쉼표 전에서 자를 수 있다.
        """
        tag_availability = f"#lists > ul > li:nth-child({str(i + 1)}) " \
                           f"> dl > dd:nth-child(4)"
        available_here_raw = \
            self.DRIV_AVAIL.find_element_by_css_selector(
                tag_availability).text.split(',')[0]
        available_here = not ('불가능' in available_here_raw)
        return available_here

    def load_detail_info(self, i):
        tag_detail_info_button = f"#lists > ul > li:nth-child({str(i + 1)}) > dl > dt > a"
        detail_button = self.DRIV_AVAIL.find_element_by_css_selector(
            tag_detail_info_button)
        detail_button_url = detail_button.get_attribute('href')
        self.DRIV_CODE.get(detail_button_url)

    def get_book_code(self):
        book_code = ''
        tag_book_code = '#printArea > div.tblType01.mt30 > table > tbody > ' \
                        'tr:nth-child(2) > td:nth-child(2)'
        try:
            book_code = self.DRIV_CODE.find_element_by_css_selector(
                tag_book_code).text
        except NoSuchElementException:
            pass
        return book_code

    def update_best_option(self, lib_name, available_here, book_code):
        self.best_option = {
            'lib_name': lib_name,
            'available': available_here,
            'book_code': book_code
        }
