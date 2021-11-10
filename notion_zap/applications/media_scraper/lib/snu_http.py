from urllib import parse

import requests
from bs4 import BeautifulSoup

from notion_zap.applications.media_scraper.common.helpers import try_func_twice


@try_func_twice
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

    lib_info = ''
    try:
        lib_info = soup.select_one(tag_lib_info).text
    except AttributeError:
        pass
    finally:
        return lib_info
