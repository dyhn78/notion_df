from urllib import parse

from notion_py.applications.media_scraper.common.helpers import try_method_twice
from notion_py.applications.media_scraper.common.selenium import retry_webdriver, \
    SeleniumScraper


class SNULibrary(SeleniumScraper):
    def __init__(self):
        super().__init__()
        self.driver = self.drivers[0]

    @try_method_twice
    @retry_webdriver
    def execute(self, book_name: str) -> str:
        self.load_search_results(book_name)
        raws = self.get_raw_strings()
        for raw in raws:
            lib_info = self.parse_lib_info(raw)
            return lib_info

    @staticmethod
    def parse_lib_info(raw_string):
        # TODO 책 제목을 출력하고, 올바른 책을 선택한 게 맞는지
        #  (화면에 출력해서?) 확인하는 간단한 기능들을 구현할 것.
        return raw_string

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
        self.driver.implicitly_wait(15)

    def get_raw_strings(self):
        tag_lib_info = 'div.result-item-text.layout-fill.layout-column.flex > ' \
                       'div.search-result-availability-line-wrapper ' \
                       '> prm-search-result-availability-line > div > div > button '
        elms_lib_info = self.driver.find_elements_by_css_selector(tag_lib_info)
        return [elm.text for elm in elms_lib_info]
