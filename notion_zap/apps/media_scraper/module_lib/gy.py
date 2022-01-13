from typing import Optional

from selenium.common.exceptions import StaleElementReferenceException

from notion_zap.apps.externals.selenium import SeleniumBase
from notion_zap.apps.media_scraper.common.helpers import remove_emoji


class GoyangLibraryAgent:
    GAJWA_LIB = '가좌도서관'
    OTHER_LIB = '고양시 상호대차'

    def __init__(self, base: SeleniumBase, book_name: str):
        self.base = base
        self.book_name = remove_emoji(book_name)

        self.available_somewhere = False
        self.best_option = {}

    def __call__(self) -> Optional[dict]:
        """
        :return: [도서관 이름: str('가좌도서관', '고양시 상호대차', '스크랩 실패'),
                    현재 대출 가능: bool,
                    서지번호: str('가좌도서관'일 경우에만 non-empty)]
        """
        self.load_search_results()

        # deal with pagination
        self.review_search_results()
        return self.best_option

    @property
    def driver(self):
        return self.base.drivers[0]

    # @property
    # def driv_code(self):
    #     return self.base.drivers[1]

    def load_search_results(self):
        # load main page
        url_main_page = 'https://www.goyanglib.or.kr/center/data/search.asp'
        self.driver.get(url_main_page)
        # self.driver.implicitly_wait(3)

        # insert_book_name
        tag_input_box = '#a_q'
        input_box = self.driver.find_element("css selector", tag_input_box)
        input_box.send_keys(self.book_name)

        # click search button
        tag_search_button = '#sb1 > a'
        search_button = self.driver.find_element("css selector",
                                                 tag_search_button)
        search_button.click()
        self.driver.implicitly_wait(3)

    def review_search_results(self):
        page_buttons = self.get_page_buttons()
        for bb, button in enumerate(page_buttons):
            try:
                if bb != 0:
                    button.click()
                    self.driver.implicitly_wait(5)
            except StaleElementReferenceException:
                return
            if not (lib_names := self.get_lib_names()):
                return
            for i, lib_name in enumerate(lib_names):
                needs_detail_info = '가좌' in lib_name
                available_here = self.get_availability(i)
                if needs_detail_info:
                    self.load_detail_info(i)
                    book_code = self.get_book_code()
                    self.update_best_option(self.GAJWA_LIB, available_here, book_code)
                    return
                elif available_here and not self.available_somewhere:
                    self.available_somewhere = True
                    self.update_best_option(self.OTHER_LIB, True, '')

    def get_page_buttons(self):
        tag_no_book = '#lists > ul > li'
        no_book = self.driver.find_elements("css selector", tag_no_book)
        if no_book and '검색하신 도서가 없습니다' in no_book[0].text:
            return []
        tag_page_buttons = '#pagelist > ul > li > a'
        page_buttons = self.driver.find_elements("css selector", tag_page_buttons)
        page_buttons = page_buttons[1:-1]
        return page_buttons

    def get_lib_names(self):
        tag_lib_name = '#lists > ul > li > dl > dd:nth-child(3)'
        elms_lib_name = self.driver.find_elements("css selector", tag_lib_name)
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
            self.driver.find_element("css selector",
                                     tag_availability).text.split(',')[0]
        available_here = not ('불가능' in available_here_raw)
        return available_here

    def load_detail_info(self, i):
        tag_detail_info_button = f"#lists > ul > li:nth-child({str(i + 1)}) > dl > dt > a"
        detail_button = self.driver.find_element("css selector",
                                                 tag_detail_info_button)
        detail_button.click()
        self.driver.implicitly_wait(3)

    def go_back(self):
        self.driver.back()

    def get_book_code(self):
        tag_book_code = '#printArea > div.tblType01.mt30 > table > tbody > ' \
                        'tr:nth-child(2) > td:nth-child(2)'
        book_code = self.driver.find_element("css selector",
                                             tag_book_code).text
        return book_code.strip()

    def update_best_option(self, lib_name, available_here, book_code):
        self.best_option = {
            'lib_name': lib_name,
            'available': available_here,
            'book_code': book_code
        }
