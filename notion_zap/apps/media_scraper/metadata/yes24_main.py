import requests
from bs4 import BeautifulSoup

from .parse_contents import parse_contents


def scrap_yes24_main(url: str) -> dict:
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html5lib')

    results = dict(
        name=get_name(soup),
        subname=get_subname(soup),
        author=get_author(soup),
        publisher=get_publisher(soup),
        page_count=get_page_count(soup),
        cover_image=get_cover_image(soup),
        contents=get_contents(soup)
    )
    return results


def get_name(soup):
    tag_name = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h2'
    try:
        name = soup.select_one(tag_name).text.strip()
        for char in '?!"':
            name = name.replace(char, '')
        return name
    except AttributeError:
        pass


def get_subname(soup):
    tag_subname = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > div > h3'
    try:
        subname = soup.select_one(tag_subname).text.strip()
        return subname
    except AttributeError:
        pass


def get_author(soup):
    tag_author = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                 'span.gd_pubArea > span.gd_auth > a'
    try:
        author = soup.select_one(tag_author).text.strip()
        return author
    except AttributeError:
        pass

    tag_author2 = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                  'span.gd_pubArea > span.gd_auth'
    try:
        author_raw = soup.select_one(tag_author2).text.strip()
        author = author_raw.strip('\n').strip().replace(' 저', '')
        return author
    except AttributeError:
        pass


def get_publisher(soup):
    tag_publisher = '#yDetailTopWrap > div.topColRgt > div.gd_infoTop > ' \
                    'span.gd_pubArea > span.gd_pub > a'
    try:
        publisher = soup.select_one(tag_publisher).text.strip()
        return publisher
    except AttributeError:
        pass


def get_page_count(soup):
    tag_page = '#infoset_specific > div.infoSetCont_wrap > div > table > ' \
               'tbody > tr:nth-child(2) > td'
    try:
        page_count_plus_etc = soup.select_one(tag_page).text
        if '쪽' in page_count_plus_etc and '확인' not in page_count_plus_etc:
            page_count_str = page_count_plus_etc.split('|')[0].strip()
            page_count = int(''.join([char for char in page_count_str
                                      if char.isnumeric()]))
            return page_count
    except AttributeError:
        pass


def get_cover_image(soup):
    tag_cover_image = '#yDetailTopWrap > div.topColLft > div.gd_imgArea > ' \
                      'span > em > img'
    try:
        cover_image = str(soup.select_one(tag_cover_image))
        if 'src' in cover_image:
            cover_image = cover_image.split('src="')[-1].split('"/>')[0].strip()
            return cover_image
    except AttributeError:
        pass


def get_contents(soup):
    tag_contents = '#infoset_toc > div.infoSetCont_wrap > div.infoWrap_txt'
    try:
        contents_html = soup.select_one(tag_contents).text
        contents = parse_contents(contents_html)
        return contents
    except AttributeError:
        pass
