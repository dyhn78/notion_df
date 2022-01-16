import requests
from bs4 import BeautifulSoup

from notion_zap.apps.media_scraper.module_meta.parse_contents import parse_contents


def scrap_yes24_main(url: str) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    results = {}
    set_name(results, soup)
    set_subname(results, soup)
    set_author(results, soup)
    set_publisher(results, soup)
    set_page_count(results, soup)
    set_cover_image(results, soup)
    set_contents(results, soup)
    return results


def set_name(results, soup):
    tag_name = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2'
    try:
        name = soup.select_one(tag_name).text.strip()
        for char in '?!"':
            name = name.replace(char, '')
        results.update(name=name)
    except AttributeError:
        pass


def set_subname(results, soup):
    tag_subname = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h3'
    try:
        subname = soup.select_one(tag_subname).text.strip()
        results.update(subname=subname)
    except AttributeError:
        pass


def set_author(results, soup):
    tag_author = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                 'span.gd_pubArea > span.gd_auth > a'
    try:
        author = soup.select_one(tag_author).text.strip()
        results.update(author=author)
        return
    except AttributeError:
        pass

    tag_author2 = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                  'span.gd_pubArea > span.gd_auth'
    try:
        author_raw = soup.select_one(tag_author2).text.strip()
        author = author_raw.strip('\n').strip().replace(' 저', '')
        results.update(author=author)
    except AttributeError:
        pass


def set_publisher(results, soup):
    tag_publisher = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                    'span.gd_pubArea > span.gd_pub > a'
    try:
        publisher = soup.select_one(tag_publisher).text.strip()
        results.update(publisher=publisher)
    except AttributeError:
        pass


def set_page_count(results, soup):
    tag_page = '#infoset_specific > div.infoSetCont_wrap > div > table > ' \
               'tbody > tr:nth-child(2) > td'
    try:
        page_count_plus_etc = soup.select_one(tag_page).text
        if '쪽' in page_count_plus_etc and '확인' not in page_count_plus_etc:
            page_count_str = page_count_plus_etc.split('|')[0].strip()
            page_count = int(''.join([char for char in page_count_str
                                      if char.isnumeric()]))
            results.update(page_count=page_count)
            return
    except AttributeError:
        pass


def set_cover_image(results, soup):
    tag_cover_image = '#yDetailTopWrap > div.topColLft > div.gd_imgArea > ' \
                      'span > em > img'
    try:
        cover_image = str(soup.select_one(tag_cover_image))
        if 'src' in cover_image:
            cover_image = cover_image.split('src="')[-1].split('"/>')[0].strip()
            results.update(cover_image=cover_image)
            return
    except AttributeError:
        pass


def set_contents(results, soup):
    tag_contents = '#infoset_toc > div.infoSetCont_wrap > div.infoWrap_txt'
    try:
        contents_html = soup.select_one(tag_contents).text
        contents = parse_contents(contents_html)
        results.update(contents=contents)
    except AttributeError:
        pass
