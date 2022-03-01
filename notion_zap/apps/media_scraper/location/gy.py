from __future__ import annotations
from typing import Optional, Callable
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement

from notion_zap.apps.media_scraper.location.struct import (
    LibraryScrapResult, LibraryScrapBase)


class GoyangLibraryScrapBase(LibraryScrapBase):
    def scrap(self, title: str) -> LibraryScrapResult:
        self.start_if_needed()
        scrap = GoyangLibraryScraper(self.drivers[0], title)
        return scrap()


class GoyangLibraryScraper:
    GAJWA_LIB = '가좌도서관'
    OTHER_LIB = '고양시 상호대차'

    def __init__(self, driver: WebDriver, title: str):
        self.driver = driver
        self.query = GoyangLibraryQueryBuilder(self.driver, title)
        self.evaluate = GoyangLibraryEvaluator(self.driver)

    def __call__(self) -> Optional[LibraryScrapResult]:
        """
        :return: [도서관 이름: str('가좌도서관', '고양시 상호대차', '스크랩 실패'),
                    현재 대출 가능: bool,
                    서지번호: str('가좌도서관'일 경우에만 non-empty)]
        """
        self.query.search_for_gajwa()
        if gajwa_option := self.evaluate():
            gajwa_option.lib_name = self.GAJWA_LIB
            return gajwa_option
        self.query.search_for_all_libs()
        if other_option := self.evaluate():
            other_option.lib_name = self.OTHER_LIB
            other_option.book_code = ''
            return other_option
        return None


class GoyangLibraryQueryBuilder:
    def __init__(self, driver: WebDriver, title: str):
        self.driver = driver
        self.title = title
        self.title_is_ready = False

    def _search_for_(self, set_options: Callable[[], None]):
        if not self.title_is_ready:
            self.load_main_page()
            self.insert_title()
        set_options()
        self.search_button.click()
        self.driver.implicitly_wait(3)

    def search_for_gajwa(self):
        return self._search_for_(self.set_options_as_gajwa_only)

    def search_for_all_libs(self):
        return self._search_for_(self.set_options_as_all_libs)

    def load_main_page(self):
        url_main_page = \
            'https://www.goyanglib.or.kr/center/menu/10003/program/30001/searchSimple.do'
        self.driver.get(url_main_page)

    def insert_title(self):
        tag = '#searchKeyword'
        input_box = self.driver.find_element("css selector", tag)
        input_box.send_keys(self.title)

    def set_options_as_all_libs(self):
        if not self.now_set_for_all_libs:
            self.checkbox_for_all_libs.click()

    def set_options_as_gajwa_only(self):
        if not self.now_set_for_all_libs:
            self.checkbox_for_all_libs.click()
        self.checkbox_for_all_libs.click()
        self.checkbox_for_gajwa.click()

    @property
    def now_set_for_all_libs(self):
        return self.checkbox_for_all_libs.get_attribute('checked')

    @property
    def checkbox_for_all_libs(self):
        tag = '#searchLibraryAll'
        return self.driver.find_element("css selector", tag)

    @property
    def checkbox_for_gajwa(self):
        tag = '#searchManageCodeArr2'
        return self.driver.find_element("css selector", tag)

    @property
    def search_button(self):
        tag = '#searchBtn'
        return self.driver.find_element("css selector", tag)


class GoyangLibraryEvaluator:
    def __init__(self, driver: WebDriver):
        self.driver = driver
        self.now_page_num = 1
        self.best_option: Optional[LibraryScrapResult] = None

    def __call__(self):
        self.evaluate()
        return self.best_option

    def evaluate(self):
        if self.has_no_result():
            return
        proceed = True
        while proceed:
            if self.evalaute_page_section():
                return
            proceed = self.move_to_next_page_section()

    def has_no_result(self):
        tag = '#bookList > div.bookList.listViewStyle > ul > li > div > p.noResult'
        return bool(self.driver.find_elements("css_selector", tag))

    def evalaute_page_section(self):
        for num in range(1, 10 + 1):
            if not self.move_page(num):
                return False
            if self.evaluate_page():
                return True

    def move_page(self, num: int):
        assert 1 <= num <= 10
        if num == self.now_page_num:
            return
        if num > self.now_page_num:
            child_num = num + 1
        else:
            child_num = num + 2
        tag = f'#bookList > div.pagingWrap > p > a:nth-child({child_num})'
        try:
            page_button = self.driver.find_element("css selector", tag)
        except NoSuchElementException:
            return False
        page_button.click()
        self.now_page_num = num
        return True

    def move_to_next_page_section(self):
        tag = '#bookList > div.pagingWrap > p > a.btn-paging.next'
        try:
            next_page_section_button = self.driver.find_element("css selector", tag)
        except NoSuchElementException:
            return False
        next_page_section_button.click()
        return True

    def evaluate_page(self):
        tag = '#bookList > div.bookList.listViewStyle > ul > li > div.bookArea'
        book_areas = self.driver.find_elements("css selector", tag)
        for book_area in book_areas:
            if self.evaluate_book_area(book_area):
                return True
        return False

    def evaluate_book_area(self, book_area: WebElement):
        parser = BookAreaParser(book_area)
        # if parser.check_title():
        book_code = parser.get_book_code()
        availability = parser.get_availability()
        del parser
        self.best_option = LibraryScrapResult(availability, book_code)
        return availability



class BookAreaParser:
    def __init__(self, book_area: WebElement):
        self.book_area = book_area

    def get_book_code(self):
        tag = 'div.bookData > div.book_dataInner > div.book_info.info02 > ' \
              'p.kor.on > span:nth-child(3)'
        element = self.book_area.find_element("css selector", tag)
        return element.text

    def get_availability(self):
        tag = 'div.bookData > div.bookBtnWrap.sRent2 > ul > li.title > span > strong'
        element = self.book_area.find_element("css selector", tag)
        return "대출가능" in element.text

    # def check_title(self):
    #     tag = 'div.bookData > div.book_dataInner > div.book_name > p.kor.on > a'
    #     element = self.book_area.find_element("css selector", tag)
    #     book_title = element.get_attribute('title')
    #     return True


