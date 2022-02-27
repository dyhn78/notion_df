from typing import Optional
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.webdriver.remote.webelement import WebElement


class LibraryScrapResult:
    def __init__(self, availability: bool, book_code=''):
        self.lib_name = ''
        self.book_code = book_code
        self.availability = availability


class GoyangLibraryAgent:
    GAJWA_LIB = '가좌도서관'
    OTHER_LIB = '고양시 상호대차'

    def __init__(self, title: str, driver: WebDriver):
        self.driver = driver
        self.title = title

        self.now_search_all = True
        self.now_page_num = 1
        self.best_option: Optional[LibraryScrapResult] = None

    def __call__(self) -> Optional[LibraryScrapResult]:
        """
        :return: [도서관 이름: str('가좌도서관', '고양시 상호대차', '스크랩 실패'),
                    현재 대출 가능: bool,
                    서지번호: str('가좌도서관'일 경우에만 non-empty)]
        """
        self.load_main_page()
        self.insert_title()
        self.search_gajwa_only()
        if self.evaluate_result():
            self.best_option.lib_name = self.GAJWA_LIB
            return self.best_option
        self.search_all_libs()
        if self.evaluate_result():
            self.best_option.lib_name = self.OTHER_LIB
            self.best_option.book_code = ''
            return self.best_option
        return None

    def load_main_page(self):
        url_main_page = \
            'https://www.goyanglib.or.kr/center/menu/10003/program/30001/searchSimple.do'
        self.driver.get(url_main_page)

    def insert_title(self):
        tag = '#searchKeyword'
        input_box = self.driver.find_element("css selector", tag)
        input_box.send_keys(self.title)

    def search_all_libs(self):
        if not self.now_search_all:
            self.toggle_all_libs()
        self.click_search_button()

    def search_gajwa_only(self):
        if not self.now_search_all:
            self.toggle_all_libs()
        self.toggle_all_libs()
        self.toggle_gajwa()
        self.click_search_button()

    def toggle_all_libs(self):
        tag = '#searchLibraryAll'
        checkbox = self.driver.find_element("css selector", tag)
        checkbox.click()

    def toggle_gajwa(self):
        tag = '#searchManageCodeArr2'
        checkbox = self.driver.find_element("css selector", tag)
        checkbox.click()

    def click_search_button(self):
        tag = '#searchBtn'
        search_button = self.driver.find_element("css selector", tag)
        search_button.click()
        self.driver.implicitly_wait(3)

    def evaluate_result(self):
        if self.has_no_result():
            return False
        proceed = True
        while proceed:
            if res := self.evalaute_page_section():
                return res
            proceed = self.move_to_next_page_section()
        return False

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


