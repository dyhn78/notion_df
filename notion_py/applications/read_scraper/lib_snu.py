from urllib import parse
from selenium.common.exceptions import NoSuchElementException

from .lib_gy import retry_webdriver, try_twice, SeleniumScraper


class SNULibrary(SeleniumScraper):
    tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex > ' \
                   'div.search-result-availability-line-wrapper ' \
                   '> prm-search-result-availability-line > div > div > button '

    @try_twice
    @retry_webdriver
    def execute(self, book_name: str) -> str:

        parsedname = parse.quote(book_name)
        url = f'https://primoapac01.hosted.exlibrisgroup.com/primo-explore/search?query=any,contains,' \
              f'{parsedname}&tab=all' \
              f'&search_scope=ALL&vid=82SNU&mfacet=rtype,include,print_book,1&mfacet=library,exclude,DPT,' \
              f'1&mfacet=library,exclude,HD_CHEM_BIO,1&mfacet=library,exclude,HD_DIGIT,1&mfacet=library,exclude,KYU,' \
              f'1&mfacet=library,exclude,MUSEUM,1&offset=0&pcAvailability=false '

        print(url)
        driver = self.drivers[0]
        driver.start_client()
        driver.get(url)
        driver.implicitly_wait(15)
        lib_info = ''
        try:
            lib_info = driver.find_element_by_css_selector(self.tag_lib_info).text
        except NoSuchElementException:
            pass
        return lib_info
        # TODO 책 제목을 출력하고, 올바른 책을 선택한 게 맞는지 (화면에 출력해서?) 확인하는
        #  간단한 기능들을 구현할 것.


"""
import requests
from bs4 import BeautifulSoup

@try_twice
def scrap_snu_library(book_name) -> str:
    parsedname = parse.quote(book_name)
    url = f'https://primoapac01.hosted.exlibrisgroup.com/primo-explore/search?query=any,contains,{parsedname}&tab=all' \
          f'&search_scope=ALL&vid=82SNU&mfacet=rtype,include,print_book,1&mfacet=library,exclude,DPT,' \
          f'1&mfacet=library,exclude,HD_CHEM_BIO,1&mfacet=library,exclude,HD_DIGIT,1&mfacet=library,exclude,KYU,' \
          f'1&mfacet=library,exclude,MUSEUM,1&offset=0&pcAvailability=false '
    response = requests.post(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex >' \
                   'div.search-result-availability-line_dict-wrapper > ' \
                   'prm-search-result-availability-line_dict > div > div > button'

    lib_info = ''
    try:
        lib_info = soup.select_one(tag_lib_info).text
    except AttributeError:
        pass
    finally:
        return lib_info
"""
