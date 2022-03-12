from urllib import parse

import requests
from bs4 import BeautifulSoup
from selenium.common.exceptions import NoSuchElementException
from selenium.webdriver.chrome.webdriver import WebDriver

from notion_zap.apps.media_scraper.location.lib_struct import LibraryScrapBase, \
    LibraryScrapResult


class SNULibraryScrapBase(LibraryScrapBase):
    def scrap(self, title: str) -> LibraryScrapResult:
        scrap = SNULibraryScraper(self.get_driver(), title)
        return scrap()


class SNULibraryScraper:
    def __init__(self, driver: WebDriver, title: str):
        self.driver = driver
        self.title = title

    def __call__(self):
        self.query()
        first_title = self.pick_first_titem()
        if lib_info := self.parse_raw_title(first_title):
            return self.format_result(lib_info)

    def query(self):
        parsedname = parse.quote(self.title)
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

    def pick_first_titem(self):
        tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex > ' \
                       'div.search-result-availability-line-wrapper ' \
                       '> prm-search-result-availability-line > div > div > button '
        try:
            return self.driver.find_element("css selector", tag_lib_info).text
        except NoSuchElementException:
            return ''

    @staticmethod
    def parse_raw_title(raw_title):
        # TODO 책 제목을 출력하고, 올바른 책을 선택한 게 맞는지
        #  (화면에 출력해서?) 확인하는 간단한 기능들을 구현할 것.
        return raw_title

    @staticmethod
    def format_result(lib_info):
        res = LibraryScrapResult(True, lib_info)
        # res.lib_name = '서울대'
        return res


# deprecated
def scrap_snu_library_depr(title) -> str:
    parsedname = parse.quote(title)
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
