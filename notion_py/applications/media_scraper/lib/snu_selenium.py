from urllib import parse
from selenium.common.exceptions import NoSuchElementException

from ..selenium import retry_webdriver, SeleniumScraper
from ..helpers import try_method_twice


class SNULibrary(SeleniumScraper):
    tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex > ' \
                   'div.search-result-availability-line-wrapper ' \
                   '> prm-search-result-availability-line > div > div > button '

    @try_method_twice
    @retry_webdriver
    def execute(self, book_name: str) -> str:

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
