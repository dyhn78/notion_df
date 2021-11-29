import time
from typing import Iterable
from urllib import parse

import requests
from bs4 import BeautifulSoup
from selenium.webdriver.chrome.webdriver import WebDriver

from notion_zap.apps.externals.selenium import retry_webdriver, SeleniumBase
from notion_zap.apps.media_scraper.common.helpers import enumerate_func


class SNULibraryAgent:
    def __init__(self, base: SeleniumBase, book_names: Iterable[str]):
        self.base = base
        if isinstance(book_names, str):
            self.book_names = [book_names]
        else:
            self.book_names = list(book_names)

    @property
    def driver(self) -> WebDriver:
        return self.base.drivers[0]

    def execute(self):
        visited = set()
        for book_name in self.book_names:
            if book_name in visited:
                continue
            if lib_info := self.search_one(book_name):
                # print(f"{lib_info=}")
                return lib_info
            visited.add(book_name)

    @retry_webdriver
    def search_one(self, book_name: str) -> str:
        self.load_search_results(book_name)
        first_title = self.select_tag()
        if lib_info := self.parse_tag(first_title):
            # print(f"{lib_info=}")
            return lib_info

    def load_search_results(self, book_name):
        parsedname = parse.quote(book_name)
        url = f'https://primoapac01.hosted.exlibrisgroup.com/primo-explore/search?' \
              f'query=any,contains,{parsedname}' \
              f'&tab=all' \
              f'&search_scope=ALL&vid=82SNU' \
              f'&mfacet=rtype,include,print_book,1' \
              f'&mfacet=library,exclude,DPT,1' \
              f'&mfacet=library,exclude,HD_CHEM_BIO,1' \
              f'&mfacet=library,exclude,HD_DIGIT,1' \
              f'&mfacet=library,exclude,KYU,1' \
              f'&mfacet=library,exclude,MUSEUM,1' \
              f'&offset=0' \
              f'&pcAvailability=false '
        self.driver.get(url)
        # implicitly-wait 기능이 서울대 도서관 홈페이지에서 제대로 작동하지 않는다.
        return url

    def select_tag(self):
        tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex > ' \
                       'div.search-result-availability-line-wrapper ' \
                       '> prm-search-result-availability-line > div > div > button '
        for _ in range(10):
            try:
                elements = self.driver.find_elements("css selector", tag_lib_info)
                lib_info = elements[0].text
                assert lib_info
                return lib_info
            except (AssertionError, IndexError):
                # print(f"{self.driver.current_url=}")
                time.sleep(1)

    @staticmethod
    def parse_tag(raw_string):
        # TODO 책 제목을 출력하고, 올바른 책을 선택한 게 맞는지
        #  (화면에 출력해서?) 확인하는 간단한 기능들을 구현할 것.
        return raw_string


# deprecated
@enumerate_func
def scrap_snu_library(book_name) -> str:
    parsedname = parse.quote(book_name)
    url = f'https://primoapac01.hosted.exlibrisgroup.com/primo-explore/search?query' \
          f'=any,contains,{parsedname}&tab=all' \
          f'&search_scope=ALL&vid=82SNU&mfacet=rtype,include,print_book,' \
          f'1&mfacet=library,exclude,DPT,' \
          f'1&mfacet=library,exclude,HD_CHEM_BIO,1&mfacet=library,exclude,HD_DIGIT,' \
          f'1&mfacet=library,exclude,KYU,' \
          f'1&mfacet=library,exclude,MUSEUM,1&offset=0&pcAvailability=false '
    response = requests.post(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex >' \
                   'div.search-result-availability-line_dict-wrapper > ' \
                   'prm-search-result-availability-line_dict > div > div > button'
    try:
        lib_info = soup.select_one(tag_lib_info).text
        return lib_info
    except AttributeError:
        pass
