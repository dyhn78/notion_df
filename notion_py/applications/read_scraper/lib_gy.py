from __future__ import annotations
from typing import Callable, Union, Optional

from selenium import webdriver
from selenium.webdriver.chrome.webdriver import WebDriver
from selenium.common.exceptions import StaleElementReferenceException, NoSuchElementException, NoSuchWindowException

from .helpers import try_twice

tag_input_box = '#a_q'
tag_search_button = '#sb1 > a'
tag_page_buttons = '#pagelist > ul > li > a'
tag_lib_names = '#lists > ul > li > dl > dd:nth-child(3)'
tags_availability = '#lists > ul > li:nth-child({}) > dl > dd:nth-child(4)'
tag_book_code = '#printArea > div.tblType01.mt30 > table > tbody > tr:nth-child(2) > td:nth-child(2)'
tags_detail_info_button = '#lists > ul > li:nth-child({}) > dl > dt > a'


def retry(method: Callable, recursion_limit=5) -> Callable:
    def wrapper(driver, recursion=recursion_limit, **kwargs):
        try:
            response = method(driver, **kwargs)
        except (NoSuchElementException or StaleElementReferenceException):
            if recursion == 0:
                raise RecursionError
            driver.stop_client()
            driver.start_client()
            response = wrapper(driver, recursion - 1)
        return response
    return wrapper


def ignore_no_window_exception(method: Callable) -> Callable:
    def wrapper(self: GoyangLibrary, **kwargs):
        try:
            result = method(self, **kwargs)
        except NoSuchWindowException:
            result = self.default_value
        return result
    return wrapper


@retry
def get_input_box(driver: WebDriver, url):
    driver.get(url)
    driver.implicitly_wait(5)
    input_box = driver.find_element_by_css_selector(tag_input_box)
    return input_box


@retry
def get_book_code(driver: WebDriver, url) -> str:
    driver.get(url)
    book_code = driver.find_element_by_css_selector(tag_book_code).text
    return book_code


class GoyangLibrary:
    chromedriver_path = ''
    str_gajwa_lib = '가좌도서관'
    str_other_lib = '고양시 상호대차'
    str_failed = '스크랩 실패'
    default_value = [str_failed, False, '']

    def __init__(self):
        self.drivers = []
        for i in range(2):
            driver = webdriver.Chrome(self.chromedriver_path)
            driver.minimize_window()
            self.drivers.append(driver)

    def execute(self, book_name) -> list[Union[str, bool]]:
        res = self.execute(book_name)
        return self.default_value if res is None else res

    @try_twice
    @ignore_no_window_exception
    def _execute_raw(self, book_name) -> Optional[list[Union[str, bool]]]:
        """
        :return: [도서관 이름: str('가좌도서관', '고양시 상호대차', '스크랩 실패'),
                    현재 대출 가능: bool,
                    서지번호: str('가좌도서관'일 경우에만 non-empty)]
        """
        url_main_page = 'https://www.goyanglib.or.kr/center/data/search.asp'

        self.drivers[0].start_client()
        input_box = get_input_box(self.drivers[0], url_main_page)
        input_box.send_keys(book_name)

        search_button = self.drivers[0].find_element_by_css_selector(tag_search_button)
        search_button.click()

        self.drivers[0].implicitly_wait(3)
        no_book = self.drivers[0].find_elements_by_css_selector('#lists > ul > li')
        if no_book and '검색하신 도서가 없습니다' in no_book[0].text:
            return None

        self.drivers[0].implicitly_wait(12)
        page_buttons = self.drivers[0].find_elements_by_css_selector(tag_page_buttons)
        page_buttons = page_buttons[1:-1]
        pages = len(page_buttons)

        available_somewhere = False
        for now_page in range(pages):
            if now_page != 0:
                try:
                    page_buttons[now_page].click()
                    self.drivers[0].implicitly_wait(5)
                except StaleElementReferenceException:
                    break

            lib_names = self.drivers[0].find_elements_by_css_selector(tag_lib_names)
            if not lib_names:
                return None

            for lib_index, lib_name_raw in enumerate(lib_names):
                # self.drivers[0].find_element_by_css_selector(tag_availability).text = '대출(가능), 예약(불가능) \n ... '
                # 여기서 split(',')[0] 하면 쉼표 전에서 자를 수 있다.
                tag_availability = tags_availability.format(str(lib_index + 1))
                available_here_str = self.drivers[0].find_element_by_css_selector(tag_availability).text.split(',')[0]
                available_here = ('불가능' in available_here_str)

                if '가좌' in lib_name_raw.text:
                    tag_detail_info_button = tags_detail_info_button.format(str(lib_index + 1))
                    detail_button = self.drivers[0].find_element_by_css_selector(tag_detail_info_button)
                    detail_button_url = detail_button.get_attribute('href')
                    try:
                        book_code = get_book_code(self.drivers[1], detail_button_url)
                    except RecursionError:
                        book_code = ''
                    return [self.str_gajwa_lib, available_here, book_code]
                else:
                    available_somewhere = available_here or available_somewhere

        return [self.str_other_lib, available_somewhere, '']
